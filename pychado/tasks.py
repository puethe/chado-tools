from . import utils, dbutils, queries, ddl
from .io import direct, essentials, ontology, fasta, gff


def create_connection_string(filename: str, dbname: str) -> str:
    """Reads database connection parameters from a configuration file and generates a connection string"""
    if not filename:
        filename = dbutils.default_configuration_file()
    connection_parameters = utils.parse_yaml(filename)
    connection_parameters["database"] = dbname
    return dbutils.generate_uri(connection_parameters)


def check_access(connection_uri: str, task: str) -> bool:
    """Checks if the database of interest exists and is accessible. If the database doesn't exist, but the
    task implies its creation, create it. Otherwise exit the program."""
    exists = dbutils.exists(connection_uri)
    if exists:
        if task in ["create", "restore"]:
            # Database already exists, we should not overwrite it. Return without further action
            print("Database already exists. Overwriting is not permitted.")
            return False
        else:
            # Database exists, that's all we need
            return True
    else:
        if task in ["create", "restore"]:
            # Database doesn't exist, but task implies its creation
            return True
        else:
            # Database doesn't exist, and task can't be completed. Return without further action
            print("Database does not exist. Task can't be completed.")
            return False


def init(command: str) -> None:
    """Initiates or resets the default connection parameters"""
    if command == "init":
        # Set the default connection parameters
        dbutils.set_default_parameters()
    elif command == "reset":
        # Reset the default connection parameters to factory settings
        dbutils.reset_default_parameters()
    else:
        print("Functionality '" + command + "' is not yet implemented.")


def run_command_with_arguments(command: str, sub_command: str, arguments, connection_uri: str) -> None:
    """Runs a specified sub-command with the supplied arguments"""

    # Run the command
    if command == "connect":
        # Connect to a PostgreSQL database for an interactive session
        dbutils.connect_to_database(connection_uri)
    elif command == "admin" and sub_command == "create":
        # Create a PostgreSQL database
        dbutils.create_database(connection_uri)
    elif command == "admin" and sub_command == "drop":
        # Drop a PostgreSQL database
        dbutils.drop_database(connection_uri)
    elif command == "admin" and sub_command == "dump":
        # Dump a PostgreSQL database into an archive file
        dbutils.dump_database(connection_uri, arguments.archive)
    elif command == "admin" and sub_command == "restore":
        # Restore a PostgreSQL database from an archive file
        dbutils.create_database(connection_uri)
        dbutils.restore_database(connection_uri, arguments.archive)
    elif command == "admin" and sub_command == "setup":
        # Setup a PostgreSQL database according to a schema
        run_setup_command(arguments, connection_uri)
    elif command == "admin" and sub_command == "grant":
        # Grant access to objects in a PostgreSQL database
        run_grant_revoke_command(arguments, connection_uri, True)
    elif command == "admin" and sub_command == "revoke":
        # Revoke access to objects in a PostgreSQL database
        run_grant_revoke_command(arguments, connection_uri, False)
    elif command == "query":
        # Query a PostgreSQL database and export the result to a text file
        query = (arguments.query or utils.read_text(arguments.input_file))
        dbutils.query_to_file(connection_uri, query, arguments.output_file, arguments.delimiter,
                              arguments.include_header)
    elif command == "extract":
        # Run a pre-compiled query against the CHADO database
        run_select_command(sub_command, arguments, connection_uri)
    elif command == "insert":
        # Insert a new entity of a specified type into the CHADO database
        run_insert_command(sub_command, arguments, connection_uri)
    elif command == "delete":
        # Delete an entity of a specified type from the CHADO database
        run_delete_command(sub_command, arguments, connection_uri)
    elif command == "import":
        # Import entities of a specified type into the CHADO database
        run_import_command(sub_command, arguments, connection_uri)
    else:
        print("Functionality '" + command + "' is not yet implemented.")


def run_setup_command(arguments, uri: str) -> None:
    # Sets up a PostgreSQL database according to a schema
    if arguments.schema_file or arguments.schema == "gmod":
        schema_file = arguments.schema_file
        if not schema_file:
            schema_file = utils.download_file(dbutils.default_schema_url())
        dbutils.setup_database(uri, schema_file)
    else:
        if arguments.schema == "basic":
            client = ddl.PublicSchemaSetupClient(uri)
        elif arguments.schema == "audit":
            client = ddl.AuditSchemaSetupClient(uri)
        else:
            client = ddl.DDLClient(uri)
        client.create()


def run_grant_revoke_command(arguments, uri: str, grant_access: bool) -> None:
    # Grant/revoke access to objects in a PostgreSQL database
    client = ddl.RolesClient(uri)
    if grant_access:
        client.grant_or_revoke(arguments.role, arguments.schema, arguments.write, True)
    else:
        client.grant_or_revoke(arguments.role, arguments.schema, False, False)


def run_select_command(specifier: str, arguments, uri: str) -> None:
    # Run a pre-compiled query against a database
    template = queries.load_query(specifier)
    if specifier == "organisms":
        query = queries.set_query_conditions(template)
    elif specifier == "cvterms":
        query = queries.set_query_conditions(template, database=arguments.database, vocabulary=arguments.vocabulary)
    elif specifier == "genedb_products":
        query = queries.set_query_conditions(template, organism=arguments.organism)
    elif specifier == "stats":
        query = queries.set_query_conditions(template, organism=arguments.organism, start_date=arguments.start_date,
                                             end_date=(arguments.end_date or utils.current_date()))
    else:
        print("Functionality 'extract " + specifier + "' is not yet implemented.")
        query = queries.set_query_conditions("")
    dbutils.query_to_file(uri, query, arguments.output_file, arguments.delimiter, arguments.include_header)


def run_insert_command(specifier: str, arguments, uri: str) -> None:
    # Insert a new entity of a specified type into a database
    client = direct.DirectIOClient(uri)
    if specifier == "organism":
        client.insert_organism(arguments.genus, arguments.species, arguments.abbreviation, arguments.common_name,
                               arguments.infraspecific_name, arguments.comment)
    else:
        print("Functionality 'insert " + specifier + "' is not yet implemented.")


def run_delete_command(specifier: str, arguments, uri: str) -> None:
    # Delete an entity of a specified type from a database
    client = direct.DirectIOClient(uri)
    if specifier == "organism":
        client.delete_organism(arguments.organism)
    else:
        print("Functionality 'delete " + specifier + "' is not yet implemented.")


def run_import_command(specifier: str, arguments, uri: str) -> None:
    """Imports data from a file into a database"""
    file = None
    if hasattr(arguments, "input_file") and arguments.input_file:
        file = arguments.input_file
    elif hasattr(arguments, "input_url") and arguments.input_url:
        file = utils.download_file(arguments.input_url)

    if specifier == "essentials":
        loader = essentials.EssentialsClient(uri, arguments.verbose)
        loader.load()
    elif specifier == "ontology":
        loader = ontology.OntologyClient(uri, arguments.verbose)
        loader.load(file, arguments.format, arguments.database_authority)
    elif specifier == "gff":
        loader = gff.GFFImportClient(uri, arguments.verbose)
        loader.load(file, arguments.organism, arguments.fasta)
    elif specifier == "fasta":
        loader = fasta.FastaImportClient(uri, arguments.verbose)
        loader.load(file, arguments.organism, arguments.sequence_type)
    else:
        print("Functionality 'import " + specifier + "' is not yet implemented.")
