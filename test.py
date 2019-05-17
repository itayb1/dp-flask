from collections import MutableMapping

def delete_keys_from_dict(dictionary, keys):
    keys_set = set(keys)  # Just an optimization for the "if key in keys" lookup.

    modified_dict = {}
    for key, value in dictionary.items():
        if key not in keys_set:
            if isinstance(value, MutableMapping):
                modified_dict[key] = delete_keys_from_dict(value, keys_set)
            elif isinstance(value, list):
                lst = []
                for v in value:
                    if isinstance(v, MutableMapping):
                        lst.append(delete_keys_from_dict(v, keys_set)) 
                        modified_dict[key] = lst
            else:
                modified_dict[key] = value  # or copy.deepcopy(value) if a copy is desired for non-dicts.
    return modified_dict