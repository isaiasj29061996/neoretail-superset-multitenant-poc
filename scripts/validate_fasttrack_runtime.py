"""Read-only proof that the running services use this exact worktree snapshot."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def command(*args):
    return subprocess.check_output(args, text=True, encoding="utf-8").strip()


def normalized(path):
    value = str(path).replace("\\", "/")
    if value.startswith("/run/desktop/mnt/host/"):
        suffix = value[len("/run/desktop/mnt/host/"):]
        value = suffix[0] + ":/" + suffix[2:]
    return value.lower().rstrip("/")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--project", default="neoretail-v9-multitenant")
    args = parser.parse_args()
    root = args.root.resolve()
    manifest, reports = {}, []
    plans = {
        "local-engine": {
            "/repo": ".", "/workspace/local-engine": "local-engine",
            "/workspace/config": "config", "/workspace/generated": "generated",
        },
        "superset": {"/app/pythonpath": "superset", "/app/config": "config", "/generated": "generated"},
        "embedded-app": {"/app/config": "config", "/app/generated": "generated"},
    }
    expected_env = {
        'superset':{'NEORETAIL_CONSUMPTION_SCHEMA':'serving'},
        'local-engine':{'NEORETAIL_CUSTOMER':'pandurata','SPARK_MASTER':'local[2]','SPARK_DRIVER_MEMORY':'1g','SPARK_LOCAL_IP':'127.0.0.1'},
        'embedded-app':{'ASSISTANT_ENABLED':'false'},
    }
    engine_files = ["customers.py","settings.py","pipeline.py","postgres_serving.py","gold_serving.py","partitioned_daily.py","partitioned_validation.py","marts.py","candidates.py","tenant_audit.py","tenant_source_audit.py"]
    for service, mounts in plans.items():
        name = f"{args.project}-{service}-1"
        info = json.loads(command("docker", "inspect", name))[0]
        assert info['Config']['Labels']['neoretail.runtime']=='multitenant-fasttrack'
        environment = dict(e.split('=',1) for e in info['Config']['Env'])
        assert all(environment.get(k)==v for k,v in expected_env[service].items()), (service,'runtime environment mismatch')
        assert normalized(info["Config"]["Labels"]["com.docker.compose.project.working_dir"]) == normalized(root), name
        actual = {m["Destination"]:m["Source"] for m in info["Mounts"] if m["Type"] == "bind"}
        for destination, relative in mounts.items():
            assert normalized(actual.get(destination, "")) == normalized(root / relative), (name, destination)
        files = {"/app/config/customers.yaml":"config/customers.yaml", "/app/config/tenants.yaml":"config/tenants.yaml"}
        if service == "local-engine":
            files = {"/workspace/config/customers.yaml":"config/customers.yaml", "/workspace/config/tenants.yaml":"config/tenants.yaml"}
            files.update({"/workspace/local-engine/neoretail_local/"+f:"local-engine/neoretail_local/"+f for f in engine_files})
            code = "import json,hashlib,pathlib,inspect; from neoretail_local import customers,postgres_serving; p="+repr(list(files))+"; print(json.dumps({'hashes':{f:hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest() for f in p},'imports':[inspect.getfile(customers),inspect.getfile(postgres_serving)]}))"
            executable = "python"
        elif service == "superset":
            files.update({
                "/app/pythonpath/neoretail_bootstrap/core/metadata.py":"superset/neoretail_bootstrap/core/metadata.py",
                "/app/pythonpath/neoretail_bootstrap/core/sql_sources.py":"superset/neoretail_bootstrap/core/sql_sources.py",
                "/app/pythonpath/bootstrap_panorama.py":"superset/bootstrap_panorama.py",
                "/app/pythonpath/bootstrap_osa_industry_certified.py":"superset/bootstrap_osa_industry_certified.py",
                "/app/pythonpath/neoretail_bootstrap/osa_certified/semantics.py":"superset/neoretail_bootstrap/osa_certified/semantics.py",
            })
            for path in (root/'superset').glob('bootstrap_*.py'):
                files['/app/pythonpath/'+path.name] = str(path.relative_to(root)).replace('\\','/')
            for path in (root/'superset/neoretail_bootstrap').rglob('*.py'):
                relative = path.relative_to(root/'superset').as_posix()
                files['/app/pythonpath/'+relative] = 'superset/'+relative
            for path in (root/'superset').glob('validate_fasttrack_*.py'):
                files['/app/pythonpath/'+path.name] = 'superset/'+path.name
            code = "import json,hashlib,pathlib,inspect; from neoretail_bootstrap.core import metadata,sql_sources; p="+repr(list(files))+"; print(json.dumps({'hashes':{f:hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest() for f in p},'imports':[inspect.getfile(metadata),inspect.getfile(sql_sources)]}))"
            executable = "/app/.venv/bin/python"
        else:
            files.update({"/app/server.js":"embedded-app/server.js","/app/tenant-registry.js":"embedded-app/tenant-registry.js"})
            code = "const fs=require('fs'),crypto=require('crypto'); const p="+json.dumps(list(files))+"; console.log(JSON.stringify({hashes:Object.fromEntries(p.map(f=>[f,crypto.createHash('sha256').update(fs.readFileSync(f)).digest('hex')])),imports:['/app/server.js','/app/tenant-registry.js']}));"
            executable = "node"
        result = json.loads(command("docker","exec",name,executable,"-c" if service != "embedded-app" else "-e",code))
        for container_path, host_path in files.items():
            expected = hashlib.sha256((root / host_path).read_bytes()).hexdigest()
            assert result["hashes"][container_path] == expected, (name,host_path)
            manifest[host_path] = expected
        reports.append({"service":service,"image_id":info["Image"],"mounts":actual,"imports":result["imports"],"hashes_verified":len(files),'runtime_env':expected_env[service]})
    for path in sorted((root/"analytics-db").glob("**/*.sql")):
        manifest[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
    print(json.dumps({"base_commit":command("git","-C",str(root),"rev-parse","HEAD"),
        "snapshot_sha256":hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest(),
        "services":reports,"source_manifest":manifest},indent=2))


if __name__ == "__main__":
    main()
