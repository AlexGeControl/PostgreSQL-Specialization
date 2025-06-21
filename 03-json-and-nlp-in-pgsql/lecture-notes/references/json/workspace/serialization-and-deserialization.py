import json
import xml.etree.ElementTree as ET
from typing import Any, Dict


def serialize_dictionary(data: Dict) -> str:
    """
    Serialize a dictionary to a JSON string.
    """
    return json.dumps(data)


def deserialize_from_json(json_string: str) -> Dict[str, Any]:
    """
    Deserialize a JSON string back to a dictionary.
    """
    return json.loads(json_string)


def deserialize_from_xml(xml_string: str) -> Dict[str, Any]:
    """
    Deserialize an XML string back to a dictionary.

    Assume the XML schema is as follows:
    <person>
        <name>Chuck</name>
        <phone type="intl">+1 734 303 4456</phone>
        <email hide="yes" />
    </person>
    """
    root = ET.fromstring(xml_string)

    return {
        "name": root.find("name").text,
        "phone": {
            "type": root.find("phone").get("type"),
            "number": root.find("phone").text,
        },
        "email": {"hide": root.find("email").get("hide")},
    }


if __name__ == "__main__":
    # Example dictionary
    example_dict = {
        "name": "Chuck",
        "phone": {"type": "intl", "number": "+1 734 303 4456"},
        "email": {"hide": "yes"},
    }

    # Serialize the dictionary
    serialized_dict = serialize_dictionary(example_dict)
    print("Serialized Python dictionary:", serialized_dict)

    # Deserialize the JSON string back to a dictionary
    deserialized_json_dict = deserialize_from_json(serialized_dict)

    # Assert that the deserialized dictionary matches the original
    assert (
        deserialized_json_dict == example_dict
    ), "Deserialized JSON dictionary does not match the original"

    # Deserialize the XM string back to a dictionary
    deserialized_xml_dict = deserialize_from_xml(
        (
            "<person>"
            f"<name>{example_dict['name']}</name>"
            f"<phone type=\"{example_dict['phone']['type']}\">{example_dict['phone']['number']}</phone>"
            f"<email hide=\"{example_dict['email']['hide']}\" />"
            "</person>"
        )
    )

    # Assert that the deserialized dictionary matches the original
    assert (
        deserialized_xml_dict == example_dict
    ), "Deserialized XML dictionary does not match the original"
