from neo4j import GraphDatabase

# Function to load data into Neo4j
def load_data(tx, G):
    for node in G.nodes:
        tx.run("CREATE (:Node {id: $id})", id=node)

    for edge in G.edges:
        tx.run("MATCH (a:Node {id: $source}), (b:Node {id: $target}) "
               "CREATE (a)-[:CONNECTED]->(b)",
               source=edge[0], target=edge[1])

# Neo4j connection parameters
uri = "bolt://localhost:7687"
user = "neo4j"
password = "abcd1234"

# Connect to Neo4j and load data
driver = GraphDatabase.driver(uri, auth=(user, password))
with driver.session() as session:
    session.write_transaction(load_data, G)

# Close the Neo4j driver
driver.close()
