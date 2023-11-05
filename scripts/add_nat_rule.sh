#!/bin/bash
# ------------------------------------------------------------------------------------ #
# This script adds a NAT rule to forward traffic to another machine taking into
# account docker stuff in iptables
#
# author: Enoc Martínez
# institution: Universitat Politècnica de Catalunya (UPC)
# email: enoc.martinez@upc.edu
# license: MIT
# created: 5/11/23
# ------------------------------------------------------------------------------------ #

set -o nounset

if [ $# != 3 ] && [  $# != 4 ] ; then
	# show usage and exit
	echo "usage $0 <source port> <destination host> <destination port> (protocol, defaults to 'tcp')"
	exit
fi

# assign arguments
src_port=$1
dst_host=$2
dst_port=$3

protocol="tcp"
if [ $# == 4 ]; then
	protocol=$4
fi

# Check if root
if [ $(whoami) != "root" ]; then
    echo "ERROR this script requires super-user permissions"
    exit 0
fi

# Start
echo "Creating a NAT from ${src_port} to  ${dst_host}:${dst_port} with protocol $protocol"

# Check if generic configuration is ready
fwd_active=$(cat /proc/sys/net/ipv4/ip_forward)
if [ $fwd_active != 1 ]; then
	echo "enabling ipv4 forwarding..."
	sysctl net.ipv4.ip_forward=1
fi
iptables -t filter --check DOCKER-USER -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT > /dev/null 2>&1
success=$?
if [ $success != 0 ]; then
	echo "setting --ctstate ESTABLISHED,RELATED rule"
	iptables -t filter -I DOCKER-USER -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
fi

# Setting iptables rules

echo "prerouting..."
iptables -t nat --check PREROUTING -p ${protocol} --dport ${src_port} -j DNAT --to-destination ${dst_host}:${dst_port}  > /dev/null 2>&1
success=$?
if [ $success != 0 ]; then
	echo "adding PREROUTING rule..."
	iptables -t nat -I PREROUTING -p ${protocol} --dport ${src_port} -j DNAT --to-destination ${dst_host}:${dst_port}
else
	echo "PREROUTING rule already set"
fi

echo "postrouting..."
iptables -t nat --check POSTROUTING -p ${protocol} --dport ${dst_port} -j MASQUERADE  > /dev/null 2>&1
success=$?
if [ $success != 0 ]; then
	echo "adding PRERPOSTROUTINGOUTING rule..."
	iptables -t nat -I POSTROUTING -p ${protocol} --dport ${dst_port} -j MASQUERADE
else
	echo "POSTROUTING rule already set"
fi


echo "docker-user..."
iptables -t filter --check DOCKER-USER -p ${protocol} --dport ${dst_port} -j ACCEPT  > /dev/null 2>&1
success=$?
if [ $success != 0 ]; then
	echo "adding DOCKER-USER rule..."
	iptables -t filter -I DOCKER-USER -p ${protocol} --dport ${dst_port} -j ACCEPT
else
	echo "DOCKER-USER rule already set"
fi


echo "done!"

