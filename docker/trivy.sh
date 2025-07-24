#!/bin/bash

set -e

image="docker.io/jgoodier/porthole:latest"
# Convert JSON results to the specified YAML format
json_file="$(date +%Y-%m-%d)-trivy-results.json"
yaml_file="$(date +%Y-%m-%d)-trivy-results.yaml"

trivy image --format json --ignore-unfixed --severity CRITICAL,HIGH  "${image}" > $json_file

if [ -f "$json_file" ]; then
  echo "Converting JSON results to YAML format..."
  
  # Process each JSON object in the file
  jq -c '.' "$json_file" | while read -r json_obj; do
    # Extract the required fields
    artifact_name=$(echo "$json_obj" | jq -r '.ArtifactName')
    
    # Start YAML output
    echo "$artifact_name:" >> "$yaml_file"
    echo "  Results:" >> "$yaml_file"
    
    # Process each result
    echo "$json_obj" | jq -c '.Results[]' | while read -r result; do
      target=$(echo "$result" | jq -r '.Target')
      echo "    \"$target\":" >> "$yaml_file"
      
      # Check if vulnerabilities exist
      if echo "$result" | jq -e '.Vulnerabilities' > /dev/null 2>&1; then
        echo "$result" | jq -c '.Vulnerabilities[]' | while read -r vuln; do
          status=$(echo "$vuln" | jq -r '.Status')
          vuln_id=$(echo "$vuln" | jq -r '.VulnerabilityID')
          severity=$(echo "$vuln" | jq -r '.Severity')
          
          echo "      - Status: $status" >> "$yaml_file"
          echo "        VulnerabilityID: $vuln_id" >> "$yaml_file"
          echo "        Severity: $severity" >> "$yaml_file"
        done
      else
        echo "--------------------------------"
        echo "No vulnerabilities found" > "$yaml_file"
      fi
    done
  done  
  echo "YAML output saved to $yaml_file"
else
  echo "No JSON results file found"
  exit 1
fi

cat "$yaml_file"
echo "--------------------------------"
echo "Total vulnerabilities: $(grep -c 'VulnerabilityID:' $yaml_file)"
echo "Note that Status: 'fixed' mean our image has fixable vulnerabilities."
