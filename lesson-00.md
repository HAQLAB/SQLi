# SQL INJECTION - LESSON 0

What is SQL Injection?
SQL Injection (SQLi) is a type of code injection technique, used to attack data-driven applications, that makes it possible to execute malicious SQL statements.

First public discussion about SQL injection appeared in 1998 on [Phrack Magazine](http://phrack.org/issues/54/8.html#article).

SQLi exploits a security vulnerability in application's software, based on weak
or absence of validation of the user inputs.

Using an SQLi allows attackers to spoof identity, tamper existing data, dump,
edit and delete all data, execute administration operation on DBMS and in
particular circumstances allows an attacker to obtain LFI or RCE on a system.

Usually an SQLi attack happens on Web applications but the only requirement
is that an input controlled by the end-user (like a search input form, a login
form, etc.) is used to create a query that will be executed on the DBMS.

## ' OR 1=1

The first basic way to check if an application is vulnerable to SQLi is to try
to break query syntax.

#### Example 0.1
Given this PHP code:
```php

  $sql = "SELECT * FROM pages WHERE id = " . $_GET['id'];
  $result = $conn->query($sql);
  while($row = $result->fetch_array()){
    print_r($row);
  }

```

If we use `$_GET['id'] = 1` we will get the page with id `1` from the DB, but
what happens if we pass `1'` as value?
```
  #1064 - You have an error in your SQL syntax; check the manual that corresponds to your MariaDB server version for the right syntax to use near ''
```

BOOM! We broke the syntax and got an error. But What happened?
Let's see the query that is created :
```
  SELECT * FROM pages WHERE id = 1'
```

The DBMS was expecting an ending quote ' that is not present and produces a
syntax error.

This is useful to understand that what we are injecting in the query was
interpreted as part of the SQL statement and not just as value that `id` should
have.

Therefore we can try to insert more complex SQL statements to see what happens:
Let's try with `$_GET[id] = 1 OR 1=1`, the query produced will be:
```
  SELECT * FROM pages WHERE id = 1 OR 1=1
```

BOOM! The resulting query is legal and we will get all the pages from the DB.

The technique is basically the same if the argument is surrounded by quotes,
we just have to break the string in SQL, inject our code and be careful that the
syntax is legal.

#### Example 0.2
Given this PHP code:

We have just introduced the surrounding single quotes `'` in the SQL
statement (the double quotes `"` are the PHP string delimiters).
```php

  $sql = "SELECT * FROM pages WHERE id = '" . $_GET['id'] . "'";
  $result = $conn->query($sql);
  while($row = $result->fetch_array()){
    print_r($row);
  }

```

Using `$_GET[id] = 1`, the query produced will be:
```
  SELECT * FROM pages WHERE id = '1'
```

If we use `$_GET[id] = 1' OR 1=1`, the query produced will be:
```
  SELECT * FROM pages WHERE id = '1' OR 1=1'
```
and we will get an SQL syntax error (and ending quote is missing).
But we can inject multiple quotes :)

Let's try with `$_GET[id] = 1' OR '1'='1` (please note the missing ending quote).
It will produce:
```
  SELECT * FROM pages WHERE id = '1' OR '1'='1'
```

BOOM! The resulting query is legal and we will get all the pages from the DB.

## LOGIN BYPASS
The technique described in the previous chapter can be useful to bypass login
screens.

#### Example 0.3
Given this PHP code:
```php

  $sql = "SELECT * FROM users
          WHERE username = '" . $_GET['username'] . "'
          AND password = '" . $_GET['password'] . "'";
  $result = mysqli_query($conn, $sql);
  $row_count = mysqli_num_rows($result);
  if ($row_count > 0) {
    echo 'Authorized';
  } else {
    echo 'Not authorized';
  }

```
If we use `$_GET['username'] = admin` and `$_GET['password'] = password` the
resulting query will be:
```
  SELECT * FROM users WHERE username = 'admin' AND password = 'password'
```
The code will check if the resulting number of rows is greater than 1, so we
need a way to alter this condition.

We will try to use `$_GET['password'] = password' OR '1'='1` for the user
`admin`.
The query produced will be:
```
  SELECT * FROM users WHERE username = 'admin' AND password = 'password' OR '1' = '1'
```

BOOM! We altered the query adding a condition that is always `true`.
Because of that the resulting number of rows will be greater than `1` and we
can access to the authenticated part of code.


### COMMENTS

### NESTED QUERIES

### STACKED QUERIES


### REAL LIFE EXAMPLES

### UNSAFE EXAMPLES

### SAFE EXAMPLES

### TOOL
