#!/usr/bin/env bash
# Shared PYTHONPATH for Peacock One (relative to the Peacock/ project root).
# Sourced by npm scripts, Makefile, and helper shells.
export PYTHONPATH="${PEACOCK_ROOT:-.}:backend:backend/packages:backend/services:engines/seo:engines/aeo:engines/geo:engines/crawler:engines/competitor-intelligence:engines/citation-intelligence:engines/content-intelligence:engines/opportunity-engine:engines/llm-intelligence:engines/ai-visibility:engines/measurement:engines/experiment-engine:engines/learning-engine:plugins:agents:experts:publishing${PYTHONPATH:+:$PYTHONPATH}"
