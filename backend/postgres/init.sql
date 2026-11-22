\getenv access_password ACCESS_DB_PASSWORD
\getenv tasks_print_password TASKS_PRINT_DB_PASSWORD
\getenv submissions_password SUBMISSIONS_DB_PASSWORD

REVOKE CONNECT ON DATABASE postgres, template1 FROM PUBLIC;

CREATE ROLE access_app LOGIN PASSWORD :'access_password';
CREATE DATABASE access OWNER access_app;
REVOKE CONNECT ON DATABASE access FROM PUBLIC;

CREATE ROLE tasks_print_app LOGIN PASSWORD :'tasks_print_password';
CREATE DATABASE tasks_print OWNER tasks_print_app;
REVOKE CONNECT ON DATABASE tasks_print FROM PUBLIC;

CREATE ROLE submissions_app LOGIN PASSWORD :'submissions_password';
CREATE DATABASE submissions OWNER submissions_app;
REVOKE CONNECT ON DATABASE submissions FROM PUBLIC;
