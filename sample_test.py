from neo4j import GraphDatabase

# Function to run Louvain algorithm
def run_louvain(tx):
    # Create a simplified graph projection with only TRANSACTION relationships
    query = (
        "CALL gds.graph.project('test_graph', '*', {TRANSACTION: {properties: 'amount'}})"
    )
    tx.run(query)

    # Run the Louvain algorithm on the test_graph
    query = (
        "CALL gds.louvain.write('test_graph', {"
        "writeProperty: 'communityId', "
        "relationshipWeightProperty: 'amount'}) "
        "YIELD communityCount, modularity, modularities"
    )
    result = tx.run(query)
    for record in result:
        print(f"Detected {record['communityCount']} communities with modularity {record['modularity']}")

# Neo4j connection parameters
uri = "bolt://localhost:7687"
user = "neo4j"
password = "abcd1234"

# Connect to Neo4j and run Louvain algorithm
driver = GraphDatabase.driver(uri, auth=(user, password))
with driver.session() as session:
    # Run Louvain algorithm
    session.write_transaction(run_louvain)

# Close the Neo4j driver
driver.close()
