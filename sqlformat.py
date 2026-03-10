#!/usr/bin/env python3
"""sqlformat - SQL formatter and linter.

One file. Zero deps. Pretty SQL.

Usage:
  sqlformat.py "SELECT * FROM users WHERE id = 1"
  sqlformat.py file.sql                    → format SQL file
  sqlformat.py file.sql --upper            → uppercase keywords
  sqlformat.py file.sql --indent 4         → custom indent
  cat query.sql | sqlformat.py -           → stdin
"""

import argparse
import re
import sys

KEYWORDS = {
    "SELECT", "FROM", "WHERE", "AND", "OR", "NOT", "IN", "EXISTS",
    "INSERT", "INTO", "VALUES", "UPDATE", "SET", "DELETE",
    "JOIN", "LEFT", "RIGHT", "INNER", "OUTER", "CROSS", "FULL", "ON",
    "GROUP", "BY", "ORDER", "ASC", "DESC", "HAVING",
    "LIMIT", "OFFSET", "UNION", "ALL", "DISTINCT", "AS",
    "CREATE", "TABLE", "ALTER", "DROP", "INDEX", "VIEW",
    "PRIMARY", "KEY", "FOREIGN", "REFERENCES", "CONSTRAINT",
    "NULL", "DEFAULT", "CHECK", "UNIQUE", "CASCADE",
    "IF", "ELSE", "THEN", "END", "CASE", "WHEN",
    "COUNT", "SUM", "AVG", "MIN", "MAX", "BETWEEN", "LIKE", "IS",
    "BEGIN", "COMMIT", "ROLLBACK", "TRANSACTION",
    "WITH", "RECURSIVE", "EXCEPT", "INTERSECT",
}

NEWLINE_BEFORE = {"SELECT", "FROM", "WHERE", "JOIN", "LEFT", "RIGHT", "INNER",
                   "GROUP", "ORDER", "HAVING", "LIMIT", "UNION", "INSERT",
                   "UPDATE", "DELETE", "SET", "VALUES", "WITH", "AND", "OR"}


def tokenize(sql: str) -> list[str]:
    tokens = []
    i = 0
    while i < len(sql):
        if sql[i] in (" ", "\t", "\n", "\r"):
            i += 1
            continue
        if sql[i] == "'" or sql[i] == '"':
            quote = sql[i]
            j = i + 1
            while j < len(sql) and sql[j] != quote:
                if sql[j] == "\\":
                    j += 1
                j += 1
            tokens.append(sql[i:j+1])
            i = j + 1
        elif sql[i:i+2] == "--":
            j = sql.index("\n", i) if "\n" in sql[i:] else len(sql)
            tokens.append(sql[i:j])
            i = j
        elif sql[i] in "(),;*":
            tokens.append(sql[i])
            i += 1
        elif sql[i:i+2] in (">=", "<=", "<>", "!=", "||"):
            tokens.append(sql[i:i+2])
            i += 2
        elif sql[i] in "=<>+-/":
            tokens.append(sql[i])
            i += 1
        else:
            j = i
            while j < len(sql) and sql[j] not in " \t\n\r(),;=<>+-*/|'\"":
                j += 1
            tokens.append(sql[i:j])
            i = j
    return tokens


def format_sql(sql: str, indent: int = 2, uppercase: bool = True) -> str:
    tokens = tokenize(sql)
    lines = []
    current_line = []
    depth = 0
    pad = " " * indent

    for i, tok in enumerate(tokens):
        upper = tok.upper()

        if upper in NEWLINE_BEFORE and current_line:
            lines.append(pad * depth + " ".join(current_line))
            current_line = []

        if tok == "(":
            depth += 1
        elif tok == ")":
            depth = max(0, depth - 1)

        if upper in KEYWORDS and uppercase:
            current_line.append(upper)
        else:
            current_line.append(tok)

        if tok == ";":
            lines.append(pad * depth + " ".join(current_line))
            current_line = []
            lines.append("")

    if current_line:
        lines.append(pad * depth + " ".join(current_line))

    return "\n".join(lines).strip()


def main():
    p = argparse.ArgumentParser(description="SQL formatter")
    p.add_argument("input", nargs="?", help="SQL string, file, or - for stdin")
    p.add_argument("--indent", type=int, default=2)
    p.add_argument("--upper", action="store_true", default=True, help="Uppercase keywords")
    p.add_argument("--no-upper", action="store_true")
    args = p.parse_args()

    if not args.input:
        p.print_help()
        return 1

    if args.input == "-":
        sql = sys.stdin.read()
    elif args.input.endswith(".sql") or "\n" not in args.input and len(args.input) > 200:
        try:
            with open(args.input) as f:
                sql = f.read()
        except FileNotFoundError:
            sql = args.input
    else:
        sql = args.input

    upper = not args.no_upper
    print(format_sql(sql, args.indent, upper))


if __name__ == "__main__":
    sys.exit(main() or 0)
