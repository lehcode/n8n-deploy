#!/usr/bin/env node
/**
 * Test script for n8n-deploy script sync testing.
 * Usage: echo '{"test": "data"}' | node test-script.js
 */

"use strict";

let data = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', (chunk) => (data += chunk));
process.stdin.on('end', () => {
  try {
    const input = JSON.parse(data);
    const result = {
      script: "test-script.js",
      timestamp: new Date().toISOString(),
      status: "success",
      input: input
    };
    console.log(JSON.stringify(result));
  } catch (e) {
    console.error(JSON.stringify({ error: e.message }));
    process.exit(1);
  }
});
