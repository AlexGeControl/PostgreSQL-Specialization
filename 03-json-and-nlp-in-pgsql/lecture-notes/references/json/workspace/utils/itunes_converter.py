#!/usr/bin/env python3
"""
iTunes Library XML to JSON Converter

This module provides functionality to convert iTunes library XML exports to JSON format.
The iTunes library XML follows Apple's Property List (plist) format and contains
library metadata, track information, and playlist definitions.

Example:
    Convert an iTunes library XML file to JSON:
    
    >>> from itunes_converter import ITunesLibraryConverter
    >>> converter = ITunesLibraryConverter()
    >>> json_data = converter.convert_file('library.xml')
    >>> converter.save_json(json_data, 'library.json')

Author: GitHub Copilot
Date: 2024
"""

import argparse
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Union
from xml.parsers.expat import ExpatError


class ITunesLibraryConverter:
    """
    Converts iTunes library XML exports to structured JSON format.
    
    This class handles the conversion of Apple Property List (plist) formatted
    iTunes library exports into clean, structured JSON. It properly handles
    all plist data types including dictionaries, arrays, strings, integers,
    dates, and booleans.
    
    Attributes:
        _plist_type_handlers (Dict[str, callable]): Mapping of plist XML tags to handler functions
    """
    
    def __init__(self) -> None:
        """Initialize the iTunes library converter with plist type handlers."""
        self._plist_type_handlers = {
            'data': self._parse_data,
            'dict': self._parse_dict,
            'array': self._parse_array,
            'string': self._parse_string,
            'integer': self._parse_integer,
            'real': self._parse_real,
            'date': self._parse_date,
            'true': self._parse_true,
            'false': self._parse_false,
        }
    
    def convert_file(self, xml_file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Convert an iTunes library XML file to JSON structure.
        
        Args:
            xml_file_path: Path to the iTunes library XML file
            
        Returns:
            Dict containing the converted library data
            
        Raises:
            FileNotFoundError: If the XML file doesn't exist
            ExpatError: If the XML file is malformed
            ValueError: If the file is not a valid iTunes library XML
            
        Example:
            >>> converter = ITunesLibraryConverter()
            >>> data = converter.convert_file('MyLibrary.xml')
            >>> print(data['Library']['Major Version'])
            1
        """
        xml_path = Path(xml_file_path)
        if not xml_path.exists():
            raise FileNotFoundError(f"XML file not found: {xml_path}")
        
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
        except ET.ParseError as e:
            raise ExpatError(f"Invalid XML format: {e}")
        
        return self._convert_plist_root(root)
    
    @staticmethod
    def save_json(input_data: Dict[str, Any], output_path: Union[str, Path], indent: int = 2) -> None:
        """
        Save converted library data to a JSON file.
        
        Args:
            input_data: The converted library data dictionary
            output_path: Path where the JSON file should be saved
            indent: Number of spaces for JSON indentation (default: 2)
            
        Raises:
            PermissionError: If unable to write to the output path
            TypeError: If data is not JSON serializable
            
        Example:
            >>> converter = ITunesLibraryConverter()
            >>> data = converter.convert_file('library.xml')
            >>> converter.save_json(data, 'library.json')
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with output_file.open('w', encoding='utf-8') as f:
                json.dump(input_data, f, indent=indent, ensure_ascii=False, default=str)
        except (OSError, IOError) as e:
            raise PermissionError(f"Unable to write to {output_path}: {e}")
        except TypeError as e:
            raise TypeError(f"Data is not JSON serializable: {e}")
    
    def _convert_plist_root(self, root: ET.Element) -> Dict[str, Any]:
        """
        Convert the root plist element to a dictionary.
        
        Args:
            root: The root XML element (should be 'plist')
            
        Returns:
            Dict containing the converted plist data
            
        Raises:
            ValueError: If the root element is not a valid plist
        """
        if root.tag != 'plist':
            raise ValueError(f"Expected 'plist' root element, got '{root.tag}'")
        
        version = root.get('version')
        if version != '1.0':
            raise ValueError(f"Unsupported plist version: {version}")
        
        # The plist should contain exactly one dict as its child
        dict_element = root.find('dict')
        if dict_element is None:
            raise ValueError("No dictionary found in plist root")
        
        return self._parse_dict(dict_element)
    
    def _parse_dict(self, element: ET.Element) -> Dict[str, Any]:
        """
        Parse a plist dictionary element.
        
        Args:
            element: XML element representing a plist dict
            
        Returns:
            Python dictionary with converted values
        """
        result = {}

        children = list(element)
        if len(children) % 2 != 0:
            raise ValueError("Invalid plist dictionary: elements must be in key-value pairs")
        
        # Dictionary elements alternate between key and value
        key_elements, value_elements = children[0::2], children[1::2]
        for key_element, value_element in zip(key_elements, value_elements):
            if key_element.tag != 'key':
                raise ValueError(f"Expected 'key' element, got '{key_element.tag}'")
            
            key, value = self._parse_data(key_element), self._parse_element(value_element)

            result[key] = value
        
        return result
    
    def _parse_array(self, element: ET.Element) -> List[Any]:
        """
        Parse a plist array element.
        
        Args:
            element: XML element representing a plist array
            
        Returns:
            Python list with converted values
        """
        return [self._parse_element(child) for child in element]

    def _parse_element(self, element: ET.Element) -> Any:
        """
        Parse any plist element based on its tag.
        
        Args:
            element: XML element to parse
            
        Returns:
            Converted Python value
            
        Raises:
            ValueError: If the element tag is not recognized
        """
        tag = element.tag
        if tag in self._plist_type_handlers:
            return self._plist_type_handlers[tag](element)
        else:
            raise ValueError(f"Unsupported plist element type: {tag}")
        
    def _parse_string(self, element: ET.Element) -> str:
        """
        Parse a plist string element.
        
        Args:
            element: XML element representing a plist string
            
        Returns:
            String value
        """
        return element.text or ''
    
    def _parse_integer(self, element: ET.Element) -> int:
        """
        Parse a plist integer element.
        
        Args:
            element: XML element representing a plist integer
            
        Returns:
            Integer value
            
        Raises:
            ValueError: If the element text is not a valid integer
        """
        text = element.text or '0'
        try:
            return int(text)
        except ValueError:
            raise ValueError(f"Invalid integer value: {text}")
    
    def _parse_real(self, element: ET.Element) -> float:
        """
        Parse a plist real (float) element.
        
        Args:
            element: XML element representing a plist real
            
        Returns:
            Float value
            
        Raises:
            ValueError: If the element text is not a valid float
        """
        text = element.text or '0.0'
        try:
            return float(text)
        except ValueError:
            raise ValueError(f"Invalid real value: {text}")
    
    def _parse_date(self, element: ET.Element) -> str:
        """
        Parse a plist date element.
        
        Args:
            element: XML element representing a plist date
            
        Returns:
            ISO formatted date string
            
        Raises:
            ValueError: If the element text is not a valid ISO date
        """
        text = element.text or ''
        try:
            # Validate the date format and return as string
            datetime.fromisoformat(text.replace('Z', '+00:00'))
            return text
        except ValueError:
            raise ValueError(f"Invalid date format: {text}")
    
    def _parse_true(self, element: ET.Element) -> bool:
        """
        Parse a plist true element.
        
        Args:
            element: XML element representing a plist true value
            
        Returns:
            Boolean True
        """
        return True
    
    def _parse_false(self, element: ET.Element) -> bool:
        """
        Parse a plist false element.
        
        Args:
            element: XML element representing a plist false value
            
        Returns:
            Boolean False
        """
        return False
    
    def _parse_data(self, element: ET.Element) -> str:
        """
        Parse a plist data element.
        
        Args:
            element: XML element representing a plist data value
            
        Returns:
            Base64 encoded data as string
        """
        return element.text or ''
    

def extract_library_metadata(library_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract library metadata from converted iTunes library data.
    
    Args:
        library_data: Converted iTunes library dictionary
        
    Returns:
        Dictionary containing library metadata fields
        
    Example:
        >>> data = converter.convert_file('library.xml')
        >>> metadata = extract_library_metadata(data)
        >>> print(metadata['Application Version'])
        '12.3.1.23'
    """
    metadata_fields = [
        'Major Version', 
        'Minor Version', 
        'Date', 
        'Application Version',
        'Features', 
        'Show Content Ratings', 
        'Music Folder', 
        'Library Persistent ID'
    ]
    
    metadata = {}
    for field in metadata_fields:
        if field in library_data:
            metadata[field] = library_data[field]
    
    return metadata


def extract_tracks(library_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Extract track information from converted iTunes library data.
    
    Args:
        library_data: Converted iTunes library dictionary
        
    Returns:
        Dictionary mapping track IDs to track metadata
        
    Example:
        >>> data = converter.convert_file('library.xml')
        >>> tracks = extract_tracks(data)
        >>> track_id = list(tracks.keys())[0]
        >>> print(tracks[track_id]['Name'])
        'Song Title'
    """
    return library_data.get('Tracks', {})


def extract_playlists(library_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract playlist information from converted iTunes library data.
    
    Args:
        library_data: Converted iTunes library dictionary
        
    Returns:
        List of playlist dictionaries
        
    Example:
        >>> data = converter.convert_file('library.xml')
        >>> playlists = extract_playlists(data)
        >>> print(playlists[0]['Name'])
        'My Playlist'
    """
    return library_data.get('Playlists', [])


def get_track_statistics(tracks: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate statistics about the track collection.
    
    Args:
        tracks: Dictionary of track data
        
    Returns:
        Dictionary containing track statistics
        
    Example:
        >>> tracks = extract_tracks(library_data)
        >>> stats = get_track_statistics(tracks)
        >>> print(f"Total tracks: {stats['total_tracks']}")
    """
    if not tracks:
        return {
            'total_tracks': 0,
            'total_time': 0,
            'genres': [],
            'artists': [],
            'albums': []
        }
    
    total_time = 0
    genres = set()
    artists = set()
    albums = set()
    
    for track_data in tracks.values():
        # Total time in milliseconds
        if 'Total Time' in track_data:
            total_time += track_data['Total Time']
        
        # Collect unique values
        if 'Genre' in track_data:
            genres.add(track_data['Genre'])
        if 'Artist' in track_data:
            artists.add(track_data['Artist'])
        if 'Album' in track_data:
            albums.add(track_data['Album'])
    
    return {
        'total_tracks': len(tracks),
        'total_time_ms': total_time,
        'total_time_hours': total_time / (1000 * 60 * 60),
        'unique_genres': len(genres),
        'unique_artists': len(artists),
        'unique_albums': len(albums),
        'genres': sorted(list(genres)),
        'artists': sorted(list(artists)),
        'albums': sorted(list(albums))
    }


def save_library_data_to_folder(
    input_filepath: Union[str, Path], 
    output_folder: Union[str, Path], 
    library_data: Dict[str, Any]
) -> None:
    """
    Save iTunes library data to multiple JSON files in the specified folder.
    
    Args:
        input_filepath: Path to the original XML file (used for naming the main JSON file)
        output_folder: Path to the folder where JSON files will be saved
        library_data: Converted iTunes library data dictionary
        
    Saves:
        - {input_basename}.json: Complete library data
        - metadata.json: Library metadata
        - tracks.json: Track information
        - playlists.json: Playlist information
        - stats.json: Track statistics
    """
    input_path = Path(input_filepath)
    output_dir = Path(output_folder)
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Extract data components
    metadata = extract_library_metadata(library_data)
    tracks = extract_tracks(library_data)
    playlists = extract_playlists(library_data)
    stats = get_track_statistics(tracks)
    
    # Save complete library data with same basename as input file
    main_output_file = output_dir / f"{input_path.stem}.json"
    ITunesLibraryConverter.save_json(library_data, main_output_file)
    print(f"Saved complete library data to: {main_output_file}")
    
    # Save individual components
    components = {
        'metadata': metadata,
        'tracks': tracks,
        'playlists': playlists,
        'stats': stats
    }
    
    for name, data in components.items():
        output_file = output_dir / f"{name}.json"
        ITunesLibraryConverter.save_json(data, output_file)
        print(f"Saved {name} to: {output_file}")


def main() -> None:
    """
    Main function that handles command-line arguments and processes iTunes library conversion.
    """
    parser = argparse.ArgumentParser(
        description="Convert iTunes library XML exports to JSON format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s library.xml ./output/
  %(prog)s data/itunes-library-excerpt.xml /path/to/output/folder/

This will create multiple JSON files in the output folder:
  - {input_basename}.json (complete library data)
  - metadata.json (library metadata)
  - tracks.json (track information)
  - playlists.json (playlist information)
  - stats.json (track statistics)
        """
    )
    
    parser.add_argument(
        'input_filepath',
        type=str,
        help='Path to the iTunes library XML file to convert'
    )
    
    parser.add_argument(
        'output_folder',
        type=str,
        help='Path to the folder where JSON files will be saved'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Print detailed statistics after conversion'
    )
    
    args = parser.parse_args()
    
    # Validate input file
    input_path = Path(args.input_filepath)
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        return
    
    if not input_path.is_file():
        print(f"Error: Input path is not a file: {input_path}")
        return
    
    # Convert the library
    try:
        print(f"Converting iTunes library: {input_path}")
        converter = ITunesLibraryConverter()
        library_data = converter.convert_file(input_path)
        
        # Save to multiple JSON files
        save_library_data_to_folder(input_path, args.output_folder, library_data)
        
        # Print statistics if verbose mode is enabled
        if args.verbose:
            metadata = extract_library_metadata(library_data)
            tracks = extract_tracks(library_data)
            playlists = extract_playlists(library_data)
            stats = get_track_statistics(tracks)
            
            print(f"\nLibrary Statistics:")
            print(f"  Application Version: {metadata.get('Application Version', 'Unknown')}")
            print(f"  Library Date: {metadata.get('Date', 'Unknown')}")
            print(f"  Total Tracks: {stats['total_tracks']:,}")
            print(f"  Total Playlists: {len(playlists):,}")
            print(f"  Unique Genres: {stats['unique_genres']:,}")
            print(f"  Unique Artists: {stats['unique_artists']:,}")
            print(f"  Unique Albums: {stats['unique_albums']:,}")
            print(f"  Total Time: {stats['total_time_hours']:.2f} hours")
            
            if stats['genres']:
                print(f"  Top 5 Genres: {', '.join(stats['genres'][:5])}")
        
        print(f"\nConversion completed successfully!")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except ExpatError as e:
        print(f"Error: Invalid XML format - {e}")
    except ValueError as e:
        print(f"Error: Invalid iTunes library format - {e}")
    except Exception as e:
        print(f"Error: Unexpected error occurred - {e}")


if __name__ == '__main__':
    main()
