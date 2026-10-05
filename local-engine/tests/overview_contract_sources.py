"""Read the entrypoint and canonical Overview contracts for existing assertions."""


def read_overview(root):
    paths = [root / 'superset/bootstrap_overview.py']
    paths.extend(root / 'superset/neoretail_bootstrap/overview' / (name + '.py')
                 for name in ('semantics', 'filters', 'presentation'))
    return '\n'.join(path.read_text(encoding='utf-8') for path in paths)
