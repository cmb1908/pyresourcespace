def add(self: dict, other: dict) -> None:
    for key, value in other.items():
        if key in self:
            if type(self[key]) is dict:
                add(self[key], other[key])
            else:
                self[key] += value  # Add values for common keys
        else:
            self[key] = value  # Add new keys


class MergeDict(dict):
    def __add__(self, other: dict):
        """
        Merges another dictionary into this one, adding values for common keys.

        Args:
            other (dict): The dictionary to merge with this one.

        Returns:
            MergeDict: The updated dictionary after merging.
        """
        add(self, other)
        return self
