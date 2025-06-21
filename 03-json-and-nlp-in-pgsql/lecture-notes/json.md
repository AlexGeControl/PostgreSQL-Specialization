# Introduction to JSON

---

## Introduction to Data Serialization

Each programming language has ways of representing the two core types of collections.

| Language   | Linear Structure       | Key/Value Structure            |
|------------|------------------------|--------------------------------|
| Python     | list() [1,2,3]         | dict() {'a': 1, 'b': 2}        |
| JavaScript | Array [1,2,3]          | Object {'a': 1, 'b': 2}        |
| PHP        | Array array(1,2,3)     | AssociativeArray array('a' => 1, 'b' => 1)|
| Java       | ArrayList              | HashMap                        |

In order to move structured data between applications, we need a **language independent** syntax to move the data. If for example, we want to send a dictionary from Python to PHP we would take the following steps:

- Within Python, we would convert the dictionary to this "independent format" (**serialization**) and write it to a file.
- Within PHP we would read the file and convert it to an associative array (**de-serialization**).

Another term for **serialization and deserialization** is **marshalling and unmarshalling**.

A long time ago we used **XML** as this "format to move data structures between various languages". Here is a XML example for key-value mapping representation:

```xml
<array>
    <entry>
       <key>a</key>
       <value>1</value>
    <entry>
    <entry>
       <key>b</key>
       <value>2</value>
    </entry>
</array>
```

XML (like HTML) is a good syntax to represent documents, but it is not a natural syntax to represent lists or dictionaries. We have been using XML as a way to represent structured data for interchange since the 1990's. Before that we had serialization formats like ASN.1 fsince the mid-1980s. And formats like Comma-Separated Values (CSV) work for linear structures but not so much for key value structures.

Around 2000, we started seeing the need to move structured data between code written in JavaScript in browsers (front-end) and code running on the servers (back-end). Initially the format of choice was XML resulting in a programming pattern called **AJAX - Asynchronous JavaScript And XML**. Many programming already had libraries to read and write XML syntax so it was an obvious place to start. And in the browser, XML looked a lot like HTML so it seemed to make sense there as well.

The problem was that the structures we used in programs (list and key/value) were pretty inelegant when expressed in XML, makeing the XML hard to read and a good bit of effort to convert.

---

## The Advent of JavaScript Object Notation

Given the shortcomings of XML to represent linear and key/value structures, as more and more applications, started to transfer data between JavaScript on the browser front-end and the databases on the server back-end, Douglas Crockford noticed that the syntax for JavaScript constants might be a good serialization format. In particular, JavaScript already understood the format natively:

```html
<script type="text/javascript">
who = {
    "name": "Chuck",
    "age": 29,
    "college": true,
    "offices" : [ "3350DMC", "3437NQ" ],
    "skills" : { "fortran": 10, "C": 10,
        "C++": 5, "python" : 7 }
};
console.log(who);
</script>
```

It turned out to be easier to add libraries to the back-end languages like Python, PHP, and Java to convert their data structures to JSON than to use XML to serialize data because the back-end languages were already good at XML. The reason was really because XML did a bad job of representing linear or key/value structures that are widely used across all languages.

To help advance adoption in an industry that was (at the time) obsessed with XML, Douglas Crockford wrote a simple specification for "JSON", and put it up at [www.json.org](https://www.json.org/json-en.html) and programmers started to use it in their software development.

In order to make parsing and generating JSON simpler, JSON required all of the keys of key value pairs be surrounded by double quotes.

For those familiar with Python, JSON looks almost exactly like nested Python list and dictionary constants. And while Python was not so popular in 2001, now almost 20 years later, with Python and JavaScript emerging as the most widely used languages, it makes reading JSON pretty natural for those skilled in either language.

JSON has quickly become the dominant way to store and transfer data structures between programs. JSON is sent across networks, stored on files, and stored in databases. As JavaScript became an emerging server language with the development of the [NodeJS](https://nodejs.org/en/) web server and JSON specific databases like [MongoDB](https://www.mongodb.com/) were developed, JSON is now used for all but a few data serialization use cases. For those document-oriented use cases like [Microsoft Office XML formats](https://en.wikipedia.org/wiki/Microsoft_Office_XML_formats), XML is still the superior solution.

Database systems like Oracle, SQLServer, PostgreSQL, and MySQL have been adding native JSON columns to suport document-style storage in traditional relational databases.

---

## JSON in Python

See the sample Python code for JSON and XML de-serialization [here](references/json/workspace/serialization-and-deserialization.py)

Below is an in-depth comparison between JSON and XML provided by Claude Sonnet 4 MAX:

### Structural Impedance Mismatch
XML is a tree based approach (neither a list nor a dictionary) we have to use `find()` function in Python to query the tree, figure out its structure and manually transform the data tree into Python native data types. This is the impedance mismatch between the "shape" of XML and the "shape" of data structures inside Python.

- **JSON** Maps directly to programming language primitives (objects, arrays, primitives)
- **XML** Represents a document tree structure that requires transformation

### Performance and Parsing Characteristics
Beyond the structural differences, there are practical implications:

- JSON Advantages
  - **Faster Parsing** Native support in JavaScript, simpler parsers in other languages
  - **Smaller Payload** Less verbose syntax reduces network overhead
  - **Lower Memory Footprint** Direct mapping to language structures
  - **Streaming-Friendly** Can be parsed incrementally more easily

- XML Advantages
  - **Schema Validation** XSD provides robust type checking and validation
  - **Namespaces** Avoid naming conflicts in complex documents
  - **Mixed Content** Can handle text with embedded markup naturally
  - **Attributes vs Elements** Provides semantic distinction for metadata

### Modern Context and Ecosystem
Although JSON has won the web API world, XML is still better than JSON when representing things like hierarchical documents. Also XML is a bit more verbose and as such a bit more self-documenting as long as the XML tags have reasonable names.

- JSON has won for APIs because:
  - RESTful services predominantly use JSON
  - NoSQL databases (MongoDB, CouchDB) use JSON-like structures natively
  - Frontend frameworks expect JSON responses

- XML remains dominant for:
  - Configuration files (Maven, Spring, etc.)
  - Document formats (DOCX, SVG, XHTML)
  - Enterprise messaging (SOAP, though declining)
  - Standards requiring rich metadata and validation

### Type System Considerations

- JSON only has limited type system:
  - No native date/time types
  - No distinction between integers and floats in some implementations
  - No comments (though this can be seen as a feature)
  - No binary data support

- XML with XSD can enforce rich typing, while JSON often requires application-level validation.
  - **XSD (XML Schema Definition)** is a language for describing and validating the structure of XML documents. Think of it as a "blueprint" or "contract" that defines what elements, attributes, and data types are allowed in an XML document.
  - Without XSD, XML is just structured text with no validation rules. XSD provides:
    - **Structure validation** What elements can appear where
    - **Data type validation** Ensuring values are integers, dates, etc.
    - **Business rules** Enforcing constraints like required fields

  - See the example below for the sample XML schema definition and its instantiation:
    ```xsd
    <?xml version="1.0" encoding="UTF-8"?>
    <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
        
        <xs:element name="person">
            <xs:complexType>
                <xs:sequence>
                    <xs:element name="name" type="xs:string"/>
                    <xs:element name="age" type="xs:int"/>
                    <xs:element name="email" type="xs:string"/>
                </xs:sequence>
            </xs:complexType>
        </xs:element>
        
    </xs:schema>
    ```
    ```xml
    <person>
        <name>John Doe</name>
        <age>25</age>
        <email>john@example.com</email>
    </person>
    ```

### Python Examples

There are two Python examples on serialization and de-serialization using XML and JSON

```bash
# basic:
uv run serialization-and-deserialization.py
# advanced:
uv run utils/itunes_converter.py data/itunes-library.xml data/itunes-library
```

---

## JSON in PostgreSQL

There are three supported column types in PostgreSQL that handle key/value or JSON data. 

- **HSTORE** is a column type that can store keys and values. 

  - It is essentially a column that resembles a PHP associative array or Python dictionary, but it does not support nested data structures.
  
  - HSTORE stores key/value pairs efficiently and has good support for indexes, allowing WHERE clauses to look inside the column efficiently.

  - Indexes on HSTORE columns are easy to create and use.

  ```psql
  /*
    - hstore is a flat key/value datatype
    - you don't have to define the key-value schema ahead of time, you can simply insert the record into the table
  */
  CREATE TABLE products (
    id serial PRIMARY KEY,
    name varchar,
    attributes hstore
  );

  INSERT INTO products (name, attributes) VALUES (
    'Geek Love: A Novel',
    'author    => "Katherine Dunn",
    pages     => 368,
    category  => fiction'
  );

  SELECT name, attributes->'author' as author
  FROM products
  WHERE attributes->'category' = 'fiction'
  ```

  - **Use Case**: HSTORE is ideal for simple key/value pairs where nesting is not required. It is particularly useful for applications that need fast lookups and indexing on flat key/value data.

- **JSON** (introduced in PostgreSQL 9.2) is best thought of as **a pre-release of JSONB**.

  - A JSON column is essentially **a glorified TEXT column** with 
    
    - A TEXT type with JSON format validation

    - Built-in functions that prevent developers from creating their own JSON-like TEXT columns. 
  
  - JSON operators and functions were carried over into JSONB, bringing the best of JSON forward. 
  
  - This "layer of functions and indexes" on top of a TEXT column was a strategy used by relational databases to quickly build and release JSON support to counter the move to NoSQL databases.

  - **Use Case**: JSON is useful for applications that need to store JSON data but do not require advanced indexing or frequent querying of nested structures. It is also slightly faster for write-heavy workloads compared to JSONB because of the simpler validation used.

- **JSONB** (since PostgreSQL 9.4) is a completely new column type that combines the efficient storage and indexing of `HSTORE` with the rich operator and function support of `JSON`. The "B" stands for "better" or "binary," acknowledging that **it is no longer a big TEXT column** containing a JSON string but rather a compressed and more efficient for storage.

  - Stores the parsed JSON densely to save space.
    
  - Makes indexing more effective.
    
  - Enables efficient JSON-specific query and retrieval.

  ```psql
  /*
    - JSONB is a true JSON datatype
    - JSONB stays schema-less
  */
  CREATE TABLE integrations (id UUID, data JSONB);

  -- use GIN for indexing every key and value in the JSON attribute
  CREATE INDEX idx_integrations_data ON integrations USING gin(data);

  INSERT INTO integrations VALUES (
    uuid_generate_v4(),
    '{
      "service": "salesforce",
      "id": "AC347D212341XR",
      "email": "craig@citusdata.com",
      "occurred_at": "8/14/16 11:00:00",
      "added": {
        "lead_score": 50
      },
      "updated": {
        "updated_at": "8/14/16 11:00:00"
      }
    }');

  INSERT INTO integrations (
    uuid_generate_v4(),
    '{
      "service": "zendesk",
      "email": "craig@citusdata.com",
      "occurred_at": "8/14/16 10:50:00",
      "ticket_opened": {
        "ticket_id": 1234,
        "ticket_priority": "high"
      }
    }');
  ```
  - **Use Case**: JSONB is the go-to choice for most applications. It is optimized for querying, indexing, and storage, making it ideal for scenarios where JSON data needs to be frequently queried or manipulated.

  - **NOTE**: JSONB isn't always a fit in every data model. Where you can normalize there are benefits, but if you do have a schema that has a large number of optional columns (such as with event data) or the schema differs based on tenant id then JSONB can be a great fit.

### Choosing Between HSTORE, JSON, and JSONB

While JSONB is the most versatile and widely recommended option, there are still situations where `HSTORE` or `JSON` might be preferable:

- **HSTORE**: Best for flat key/value pairs without nesting. It is faster for simple lookups and consumes less storage for small datasets.
- **JSON**: Suitable for write-heavy workloads where indexing is not required. It is also useful for backward compatibility with older PostgreSQL versions.
- **JSONB**: Ideal for complex JSON structures, frequent querying, and indexing. It is the most future-proof option as PostgreSQL continues to optimize JSONB performance.

### Performance Considerations

According to the blog post, JSONB offers significant advantages in terms of performance:

- **Query Speed**: JSONB supports indexing on JSON paths, enabling faster queries compared to JSON and HSTORE.
- **Storage Efficiency**: JSONB compresses data more effectively, reducing storage requirements.
- **Flexibility**: JSONB supports advanced operators and functions, making it easier to work with nested JSON structures.

For most applications, JSONB is the recommended choice due to its balance of performance, flexibility, and future-proofing. However, developers should evaluate their specific use case to determine the best fit.

### Indexing: Types and Performance Implications

#### GIN (Generalized Inverted Index)

**GIN** is the most commonly used index type for JSONB columns and provides excellent performance for containment queries.

It supports two operator classes:

- `jsonb_ops` (default): Indexes all keys and values separately
- `jsonb_path_ops` Indexes only the full path-value combinations (smaller, faster for containment)

Here is an illustrative example. Given the following JSONB attribute

```json
{
  "a": {
    "b": 1, 
    "c": 2
  }
}
```

- `jsonb_ops` (default): Indexes all keys `a`, `b`, `c` and all values `1` and `2`
- `jsonb_path_ops` Indexes the following two full path to value pairs:
  - `a.b` -> `1`
  - `a.c` -> `2`

Thus, 

- For path based containment operator `@>`, `jsonb_path_ops` can provide better performance using smaller index size.
- For general key existance operator `?` and other general JSON operator, use `jsonb_ops`

Below are the performance characteristics of using GIN on JSONB:
- **Best for**: Containment queries (`@>`, `<@`), existence checks (`?`, `?&`, `?|`)
- **Query types**: `WHERE jsonb_column @> '{"key": "value"}'`
- **Size**: Larger index size but faster queries
- **Write performance**: Slower updates due to index maintenance

####  B-tree Indexes on Extracted Values

For **frequent queries on specific JSON paths**, the default B-tree indexes on extracted values often provide the best performance.

### References

- [Unstructured Datatypes in PostgreSQL - Hstore vs. JSON vs. JSONB](https://www.citusdata.com/blog/2016/07/14/choosing-nosql-hstore-json-jsonb/)

- [PostgreSQL - The NoSQL Database](https://www.linuxjournal.com/content/postgresql-nosql-database)

Below are the performance Characteristics:
- **Best for**: Equality, range, and ordering queries on specific paths
- **Query types**: `WHERE jsonb_column->>'status' = 'active'`
- **Size**: Small and efficient

#### Index Design Patterns

##### Partial Indexes

Combine indexing strategies with filtering conditions to optimize for specific use cases.

````sql
-- Partial GIN index for active records only
CREATE INDEX idx_active_data ON table_name USING gin(jsonb_column) 
WHERE jsonb_column->>'status' = 'active';

-- Partial B-tree for recent records
CREATE INDEX idx_recent_emails ON table_name ((jsonb_column->>'email'))
WHERE (jsonb_column->>'created_at')::timestamp > NOW() - INTERVAL '30 days';
````

##### Expression Indexes

Create indexes on complex expressions or transformations of JSONB data.

````sql
-- Index on array length
CREATE INDEX idx_tags_count ON table_name ((jsonb_array_length(jsonb_column->'tags')));

-- Index on multiple extracted values
CREATE INDEX idx_user_status ON table_name ((jsonb_column->>'user_id'), (jsonb_column->>'status'));
````

#### Performance Comparison and Guidelines

##### Query Pattern Recommendations:

| Query Type | Best Index Type | Example |
|------------|----------------|---------|
| Containment (`@>`) | GIN with `jsonb_path_ops` | `data @> '{"status": "active"}'` |
| Key existence (`?`) | GIN with `jsonb_ops` | `data ? 'email'` |
| Specific path equality | B-tree on extracted value | `data->>'email' = 'user@example.com'` |
| Range queries | B-tree on extracted value | `(data->>'age')::int BETWEEN 25 AND 35` |
| Complex containment | GIN with `jsonb_ops` | `data @> '{"user": {"role": "admin"}}'` |

##### Performance Considerations:

1. **Index Size vs. Query Speed**:
   - GIN indexes are larger but provide faster containment queries
   - B-tree indexes on specific paths are smaller and faster for targeted queries

2. **Write Performance Impact**:
   - GIN indexes have higher maintenance overhead on writes
   - Multiple specific B-tree indexes may be better for write-heavy workloads

3. **Memory Usage**:
   - GIN indexes require more shared_buffers and work_mem for optimal performance
   - Consider increasing these settings for JSONB-heavy workloads

#### Best Practices:

````sql
-- For a typical application with mixed query patterns
CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    data JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- General containment queries with GIN using jsonb_path_ops
CREATE INDEX idx_events_data_gin ON events USING gin(data jsonb_path_ops);

-- Specific frequent queries with default B-Tree
CREATE INDEX idx_events_user_id ON events ((data->>'user_id'));
CREATE INDEX idx_events_event_type ON events ((data->>'event_type'));

-- Time-based queries with default B-Tree
CREATE INDEX idx_events_created_at ON events (created_at);

-- Composite for common query combinations with default B-Tree
CREATE INDEX idx_events_user_type ON events ((data->>'user_id'), (data->>'event_type'));
````

---

## Use JSONB through Python PostgreSQL Connector

See [here](references/json/workspace/README.md)