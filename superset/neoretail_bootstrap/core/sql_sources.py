"""Rewrite qualified relation schemas, never literals/comments or business SQL."""
from __future__ import annotations
import re
import os

IDENTIFIER = re.compile(r"[a-z][a-z0-9_]{0,62}\Z")
WORD = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def consumption_sql(text):
    schema = os.getenv('NEORETAIL_CONSUMPTION_SCHEMA', 'gold')
    if schema not in ('gold', 'serving'):
        raise ValueError('Unsupported consumption schema')
    return rewrite_gold_sources(text, schema)


def _jinja_end(text, position):
    ending = {'{{': '}}', '{%': '%}', '{#': '#}'}[text[position:position+2]]
    position += 2
    if ending == '#}':
        end = text.find(ending, position)
        if end < 0: raise ValueError('Unterminated Jinja comment')
        return end + 2
    quote, brackets = None, []
    while position < len(text):
        char = text[position]
        if quote:
            if char == '\\': position += 2; continue
            if char == quote: quote = None
        elif not brackets and text.startswith(ending, position):
            return position + 2
        elif char in ('"', "'"):
            quote = char
        elif char in '([{':
            brackets.append(char)
        elif char in ')]}':
            if not brackets or '([{'.index(brackets[-1]) != ')]}'.index(char):
                raise ValueError('Unbalanced Jinja brackets')
            brackets.pop()
        position += 1
    raise ValueError('Unterminated Jinja block')


def _tokens(text):
    result, position = [], 0
    while position < len(text):
        start = position
        if text[position:position+2] in ('{{','{%','{#'):
            position, kind = _jinja_end(text, position), 'template'
        elif text.startswith("--", position):
            end = text.find("\n", position)
            position = len(text) if end < 0 else end
            kind = "comment"
        elif text.startswith("/*", position):
            depth, position = 1, position + 2
            while depth and position < len(text):
                if text.startswith("/*", position): depth, position = depth + 1, position + 2
                elif text.startswith("*/", position): depth, position = depth - 1, position + 2
                else: position += 1
            if depth: raise ValueError("Unterminated SQL comment")
            kind = "comment"
        elif text[position] in ("'", '"'):
            quote, position = text[position], position + 1
            while position < len(text):
                if text[position:position+2] in ('{{','{%','{#'):
                    position = _jinja_end(text, position)
                    continue
                if text[position] == quote:
                    position += 1
                    if position < len(text) and text[position] == quote:
                        position += 1
                    else: break
                else: position += 1
            else: raise ValueError("Unterminated SQL quote")
            kind = "identifier" if quote == '"' else "literal"
        elif text[position] == "$" and (tag := re.match(r"\$[A-Za-z_0-9]*\$", text[position:])):
            delimiter = tag.group()
            end = text.find(delimiter, position + len(delimiter))
            if end < 0: raise ValueError("Unterminated dollar-quoted SQL")
            position, kind = end + len(delimiter), "literal"
        elif text[position].isspace():
            while position < len(text) and text[position].isspace(): position += 1
            kind = "space"
        elif word := WORD.match(text, position):
            position, kind = word.end(), "identifier"
        else:
            position, kind = position + 1, "punct"
        result.append([kind, text[start:position]])
    return result


def rewrite_gold_sources(text: str, target_schema: str) -> str:
    if not IDENTIFIER.fullmatch(target_schema):
        raise ValueError("Invalid target schema identifier")
    if target_schema == "gold":
        return text
    tokens = _tokens(text)
    significant = [i for i, (kind, _) in enumerate(tokens) if kind not in ("space", "comment")]
    for position, index in enumerate(significant[:-2]):
        kind, value = tokens[index]
        if kind != "identifier" or value.strip('"') != "gold": continue
        dot, relation = significant[position + 1:position + 3]
        name = tokens[relation][1].strip('"')
        if tokens[dot][1] != "." or tokens[relation][0] != "identifier": continue
        if not IDENTIFIER.fullmatch(name) or not (
            name.startswith(("nr_", "dim_", "fato_", "vw_")) or name == "calculo_oportunidades"
        ):
            raise ValueError(f"Unrecognized Gold relation: {name}")
        tokens[index][1] = target_schema
    return "".join(value for _, value in tokens)


def in_caller_transaction(text: str) -> str:
    """Remove only standalone BEGIN/COMMIT; keep all functional SQL unchanged."""
    output, statement = [], []
    for token in _tokens(text):
        statement.append(token)
        if token == ['punct', ';']:
            significant = [(k,v) for k,v in statement if k not in ('space','comment')]
            if len(significant) == 2 and significant[0][0] == 'identifier' and significant[0][1].upper() in ('BEGIN','COMMIT'):
                output.extend((k,v) for k,v in statement if k in ('space','comment'))
            else:
                output.extend(statement)
            statement = []
    output.extend(statement)
    return ''.join(v for _,v in output)
