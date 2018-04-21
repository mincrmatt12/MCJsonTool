# The data dump format

Version 1

The root should contain:
    - a version object
    - a blocks object
    - an items object

## Version object

The version object looks like this:

```json
"version": {
    "fileformat": 1,
    "mcversion": "1.12.2",
    "forgemods": [
        {
            "modid": "extrafood",
            "version": "0.0.9"
        }
    ]
}
```

- `fileformat` should be 1 for this version.
- `mcversion` should contain the minecraft version as a string that the file was exported against
- `forgemods` is a list of mod objects

### Mod object

A mod object contains two keys: `modid` and `version`. `modid` is the forge mod id, and `version` is the version string of the mod.

## Blocks object

The blocks object looks like this:

```json
"blocks": [
     {
        "id": "extrafood:testblock",
        "states": [
            [
                {
                    "someproperty": 1,
                    "someotherpoert": "yay",
                },
                "path_to_blockstate (can be resourcelocation format)",
                "lang_key"
            ]
        ]
     }
]
```

It is a list of block objects

### Block objects

Block objects contain an id and a list of state objects

#### State objects

A state object is a list of lists. Each list inside the list has three members: a definition of the blockstate, a path to blockstate json used to look it up, and the unlocalized name.
Note: this may need revising, i forget if I need the blockmodel too to get a full block definition

## Items objects

Todo