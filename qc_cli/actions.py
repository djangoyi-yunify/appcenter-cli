"""Shared action model for the qc-tools command line tools.

Each action describes its name, HTTP verb, URI path, the request
parameters (name, type, required, description), plus AI-agent friendly
metadata: a human-readable description, usage examples, and notes.

Parameter types:

- str: single string value
- int: single integer value
- list: repeated parameter, serialized as ``name.1``, ``name.2``, ...
- list_dict: list of dicts, serialized as ``name.1.subkey``, ...
- json: a JSON-encoded string value (``json_object=True`` requires a JSON
  object, not an array or scalar)
"""


class Param:
    def __init__(self, name, ptype="str", required=False, description="", json_object=False):
        self.name = name
        self.ptype = ptype
        self.required = required
        self.description = description
        # For ptype == "json": require the parsed value to be a JSON object.
        self.json_object = json_object


class Action:
    def __init__(
        self,
        name,
        verb="GET",
        path="/iaas/",
        params=None,
        table_columns=None,
        required_any=None,
        description="",
        examples=None,
        notes=None,
    ):
        self.name = name
        self.verb = verb
        self.path = path
        self.params = params or []
        self.table_columns = table_columns or []
        # Groups of parameters where at least one must be provided.
        # Each group is a list of param names; the request is invalid if
        # none of the params in a group is present.
        self.required_any = required_any or []
        # Human-readable description shown in --help and `wiki`.
        self.description = description
        # Example command lines (shown verbatim, without the leading
        # "<prog> " prefix).
        self.examples = examples or []
        # Notes / caveats shown in `wiki <command>`.
        self.notes = notes or []

    def param_names(self):
        return [p.name for p in self.params]

    def required_params(self):
        return [p.name for p in self.params if p.required]

    def required_any_groups(self):
        return self.required_any
