#!/bin/bash
# This script creates the database and the user for sensorthings-master in PostgresQL. It also creates the postgis extension

set -e
set -o errexit
set -o nounset


# Add replication

postgresql_conf="/home/postgres/pgdata/data/postgresql.conf"
pg_hba_conf="/home/postgres/pgdata/data/pg_hba.conf"

echo "ODI: Configuring pg_hba.conf"
echo "host    replication     replicator       all scram-sha-256" >> $pg_hba_conf

echo "ODI: Configuring replication"
echo "### ODI Replication Conf ###" >> $postgresql_conf
echo "wal_level = replica" >> $postgresql_conf
echo "hot_standby = on" >> $postgresql_conf
echo "max_wal_senders = 10" >> $postgresql_conf
echo "max_replication_slots = 10" >> $postgresql_conf
echo "hot_standby_feedback = on" >> $postgresql_conf
echo "password_encryption = 'scram-sha-256'" >> $postgresql_conf


if "${sta_db_replicator}" ; then
  echo "ODI: Adding replicator user..."
  # Create the replication user and replication slot
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_DB" <<-EOSQL
    CREATE USER ${sta_db_replicator_user} WITH REPLICATION LOGIN PASSWORD '$sta_db_replicator_password';
    SELECT * FROM pg_create_physical_replication_slot('replication_slot_slave1');
EOSQL
fi


echo "ODI: Setting up SensorThings database"
# Create sensorthings user
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_DB" <<-EOSQL
  CREATE ROLE $sta_db_user WITH LOGIN CREATEDB PASSWORD '$sta_db_password' SUPERUSER;
  CREATE DATABASE $sta_db_name WITH OWNER "$sta_db_user";
  \connect '$sta_db_name'
  CREATE EXTENSION IF NOT EXISTS postgis;
EOSQL


echo "ODI: Setting up readonly user..."
# Create readonly user and grant read access
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_DB" <<-EOSQL
  CREATE ROLE $sta_readonly_user WITH LOGIN CREATEDB PASSWORD '$sta_readonly_password' SUPERUSER;
  GRANT pg_read_all_data TO "$sta_readonly_user";
EOSQL


echo "ODI: Creating SensorThings API access USERS tables"
psql -v ON_ERROR_STOP=1 --username "$sta_db_user" <<-EOSQL
  CREATE TABLE IF NOT EXISTS public."USERS"
  (
      "USER_NAME" character varying(25) COLLATE pg_catalog."default" NOT NULL,
      "USER_PASS" character varying(255) COLLATE pg_catalog."default",
      CONSTRAINT "USERS_PKEY" PRIMARY KEY ("USER_NAME")
  );
EOSQL

echo "ODI: Creating SensorThings API access USER_ROLES table"
psql -v ON_ERROR_STOP=1 --username "$sta_db_user" <<-EOSQL
  CREATE TABLE IF NOT EXISTS public."USER_ROLES"
  (
      "USER_NAME" character varying(25) COLLATE pg_catalog."default" NOT NULL,
      "ROLE_NAME" character varying(15) COLLATE pg_catalog."default" NOT NULL,
      CONSTRAINT "USER_ROLES_pkey" PRIMARY KEY ("USER_NAME", "ROLE_NAME"),
      CONSTRAINT "USER_ROLES_USERS_FKEY" FOREIGN KEY ("USER_NAME")
          REFERENCES public."USERS" ("USER_NAME") MATCH SIMPLE
          ON UPDATE CASCADE
          ON DELETE CASCADE
  );
EOSQL

# Now, insert the users
psql -v ON_ERROR_STOP=1 --username "$sta_db_user" <<-EOSQL
INSERT INTO public."USERS"("USER_NAME", "USER_PASS") VALUES ('$sta_api_read_user', '$sta_api_read_password');
INSERT INTO public."USERS"("USER_NAME", "USER_PASS") VALUES ('$sta_api_write_user', '$sta_api_write_password');
INSERT INTO public."USERS"("USER_NAME", "USER_PASS") VALUES ('$sta_api_admin_user', '$sta_api_admin_password');
EOSQL

# Now, insert the roles
psql -v ON_ERROR_STOP=1 --username "$sta_db_user" <<-EOSQL
INSERT INTO public."USER_ROLES"("USER_NAME", "ROLE_NAME")	VALUES ('$sta_api_read_user', 'read');
INSERT INTO public."USER_ROLES"("USER_NAME", "ROLE_NAME")	VALUES ('$sta_api_write_user', 'read');
INSERT INTO public."USER_ROLES"("USER_NAME", "ROLE_NAME")	VALUES ('$sta_api_admin_user', 'read');

INSERT INTO public."USER_ROLES"("USER_NAME", "ROLE_NAME")	VALUES ('$sta_api_write_user', 'create');
INSERT INTO public."USER_ROLES"("USER_NAME", "ROLE_NAME")	VALUES ('$sta_api_admin_user', 'create');

INSERT INTO public."USER_ROLES"("USER_NAME", "ROLE_NAME")	VALUES ('$sta_api_write_user', 'update');
INSERT INTO public."USER_ROLES"("USER_NAME", "ROLE_NAME")	VALUES ('$sta_api_admin_user', 'update');

INSERT INTO public."USER_ROLES"("USER_NAME", "ROLE_NAME")	VALUES ('$sta_api_write_user', 'delete');
INSERT INTO public."USER_ROLES"("USER_NAME", "ROLE_NAME")	VALUES ('$sta_api_admin_user', 'delete');

INSERT INTO public."USER_ROLES"("USER_NAME", "ROLE_NAME")	VALUES ('$sta_api_admin_user', 'admin');


EOSQL

