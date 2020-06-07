import argparse
import os
import sys
from collections import deque

import yaml
import pprint

import Rx3

RX_NAMESPACE = 'tag:local:'


def load_schema(schema_file, rx):
    schemas = list(yaml.safe_load_all(open(schema_file).read()))
    tag = schemas[0]['schema']
    try:
        rx.add_prefix(tag[1:], RX_NAMESPACE + tag[1:] + '/')
    except:
        print("Warning: tag '%s' already registered" % tag)

    result = {}
    for s in schemas:
        uri = s['schema']
        if 'file' in s:
            ss = load_schema(
                os.path.join(os.path.dirname(schema_file), s['file']), rx)
            tops, s = ss
            result[uri] = s[tops]
            result.update(s)
        else:
            result[uri] = s
        if 'schema' in s:
            del s['schema']

    return (tag, result)


GRAY, BLACK = 0, 1


def _topological(graph):
    order, enter, state = deque(), set(graph), {}

    def dfs(node):
        state[node] = GRAY
        for k in graph.get(node, ()):
            sk = state.get(k, None)
            if sk == GRAY: raise ValueError("cycle")
            if sk == BLACK: continue
            enter.discard(k)
            dfs(k)
        order.appendleft(node)
        state[node] = BLACK

    while enter:
        dfs(enter.pop())
    return order


def bottom_sort(alist):
    # create dependency graph (bottom-up)
    g = {}
    for item in alist:
        kk = item
        for vk, vs in alist.items():
            if vk == item:
                continue
            vss = yaml.dump(vs)
            if kk + '\n' in vss:  # to avoid partial matches
                gv = g.get(kk, [])
                gv.append(vk)
                g[kk] = gv
    return _topological(g)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description=
        'Validate a yaml file with a given schema. If no data file is specified, the expanded schema is printed out.'
    )
    parser.add_argument('schema', help="The file with the root schema")
    parser.add_argument('data',
                        nargs='?',
                        default=None,
                        help="The data file to be validated")
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()

    try:
        rx = Rx3.Factory(register_core_types=True)
        top, schema = load_schema(args.schema, rx)
        # topologically sort this according to dependencies
        ordered_schemas = bottom_sort(schema)
        for s in ordered_schemas:
            rx.learn_type(RX_NAMESPACE + s[1:], schema[s])
        v = rx.make_schema(schema[top])

        if args.data:
            content = yaml.safe_load(open(args.data).read())
            v.validate(content)
            if args.verbose:
                print("File validated OK.")
        else:
            print("Schema:")
            print(yaml.safe_dump(schema))
            if args.verbose:
                print("Rx prefix registry:")
                pprint.pprint(rx.prefix_registry, indent=4)
                print("Rx type registry")
                pprint.pprint(rx.type_registry, indent=4)

    except Exception as e:
        print("ERROR: " + str(e), file=sys.stderr)
        sys.exit(1)
