#!/bin/bash

function usage() {
    echo "Usage: $0 [option] [value] [client/server] [mode]"
    echo "Options:"
    echo "  delay         Run delay on client/server"
    echo "  corrupt       Run corruption on client/server"
    echo "  loss          Run loss on client/server"
    echo "  dup           Run duplication on client/server"
}

function delay() {
    echo "Running $1 ms delay on $2 $3"
    tc qdisc del dev eth0 root

    if [ "$4" = "uniform" ]; then
        tc qdisc add dev eth0 root netem delay $1ms distribution uniform
    else
        tc qdisc add dev eth0 root netem delay $1ms 50ms
    fi
    python3 $2_$3.py
}

function corrupt() {
    echo "Running $1% corruption on $2 $3"
    tc qdisc del dev eth0 root
    tc qdisc add dev eth0 root netem corrupt $1%
    python3 $2_$3.py
}

function loss() {
    echo "Running $1% loss on $2 $3"
    tc qdisc del dev eth0 root
    tc qdisc add dev eth0 root netem loss $1%
    python3 $2_$3.py
}

function dup() {
    echo "Running $1% duplication on $2 $3"
    tc qdisc del dev eth0 root
    tc qdisc add dev eth0 root netem duplicate $1%
    python3 $2_$3.py
}

# Check the command and call the appropriate function
case $1 in
    delay)
        delay $2 $3 $4
        ;;
    corrupt)
        corrupt $2 $3 $4
        ;;
    loss)
        loss $2 $3 $4
        ;;
    dup)
        dup $2 $3 $4
        ;;
    *)
        echo "Invalid option: $1"
        usage
        exit 1
        ;;
esac
