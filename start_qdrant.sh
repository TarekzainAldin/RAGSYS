#!/bin/bash
cd /home/tarek/RAGSYS
./qdrant -s /home/tarek/RAGSYS/qdrant_storage &
echo "✅ Qdrant يعمل على http://localhost:6333"
