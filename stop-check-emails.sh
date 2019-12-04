#!/bin/bash
pgrep -f check_for_new_emails.py | xargs kill -9
