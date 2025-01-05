def etree_to_dict(element):
    """
    Recursively converts an lxml.etree.Element into a native Python dictionary.

    Args:
        element (etree.Element): The XML element to convert.

    Returns:
        dict or str: A Python dictionary representing the XML structure,
                     or a string if the element contains only text.
    """
    # If the element has no children, return its text or an empty string
    if len(element) == 0 and len(element.attrib) == 0:
        return element.text or ""

    # Otherwise, convert its children into a dictionary
    result = {}
    for child in element:
        child_result = etree_to_dict(child)
        tag = child.tag

        # If the tag already exists, turn it into a list or append to it
        if tag in result:
            if not isinstance(result[tag], list):
                result[tag] = [result[tag]]  # Convert to a list if not already
            result[tag].append(child_result)
        else:
            result[tag] = child_result

    # Include attributes as a special "_attributes" key
    if element.attrib:
        result["_attributes"] = dict(element.attrib)
    result["text"] = element.text or ""

    return result
