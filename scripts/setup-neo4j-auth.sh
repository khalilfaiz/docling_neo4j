#!/bin/bash

echo "Neo4j Authentication Setup"
echo "========================="
echo ""
echo "Neo4j is running locally at http://localhost:7474"
echo ""
echo "First time setup:"
echo "1. Open http://localhost:7474 in your browser"
echo "2. Login with:"
echo "   - Username: neo4j"
echo "   - Password: neo4j"
echo "3. You'll be prompted to set a new password"
echo ""
echo "Then update your .env file with the new password:"
echo "NEO4J_PASSWORD=your_new_password_here"
echo ""
echo "If you want to use the default password 'your_secure_password',"
echo "set that as your new password in the Neo4j Browser."
echo ""
echo "Press Enter when you've set the password..."
read

echo "Testing connection..."
python -c "
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
load_dotenv()

uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
user = os.getenv('NEO4J_USER', 'neo4j')
password = os.getenv('NEO4J_PASSWORD', 'your_secure_password')

try:
    driver = GraphDatabase.driver(uri, auth=(user, password))
    with driver.session() as session:
        result = session.run('RETURN 1 as test')
        if result.single()['test'] == 1:
            print('✓ Connection successful!')
        driver.close()
except Exception as e:
    print(f'✗ Connection failed: {e}')
    print('Please check your password in .env file')
"
