#!/bin/bash
exe="python3"

# # list here your example snippets
codes="hello_world.py parent_child.py example_server.py example_server2.py"

for i in $codes
do
    echo $i
    $exe pyeval.py -f $i > $i"_"
done
