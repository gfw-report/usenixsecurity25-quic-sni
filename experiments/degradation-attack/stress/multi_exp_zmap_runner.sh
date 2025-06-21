#!/bin/bash

#seconds=14400
seconds=7200
ttl=20

while IFS='' read -r payload; do

	if [[ $payload =~ ^#+ ]];
	then
		continue
	else
		decrease_factor=$(echo "${#payload}" | awk '{print $0/2/267}') 
		# 267 is the length of the QUIC payload (in bytes) that we know overwhelms the censor when sent in a rate of 1gbps
		bandwidth=$(echo "$decrease_factor" | awk '{print int(1000/$0)}')
		echo $decrease_factor $bandwidth

		#timeout $seconds zmap 8.147.0.0/16 --probe-ttl=$ttl -M udp -O csv -s 65535 -p 1-65534 --probe-args=hex:$payload -B 800M
		#timeout $seconds zmap 8.144.0.0/14 --probe-ttl=$ttl -M udp -O csv -s 65535 -p 1-65534 --probe-args=hex:$payload -B "$bandwidth"M

	fi

done < payloads.txt


# This payload is known to overwhelm the censor at 1gbps. Let's try to see if we can overwhelm the censor with it using a smaller sending rate (215)
#timeout $seconds zmap 8.144.0.0/14 --probe-ttl=$ttl -M udp -O csv -s 65535 -p 1-65534 --probe-args=hex:c500000001108144962187fccea82488d99a65bb901e107bcbc370f1173b1983705b16cb2417d70040e1ed2f311bcfba704fe886c7c9c1332fb7a803cec479e5be90a2178c3cbef7de2cee8d67775520c938e2cd048830858fa9b5bdae17332de69ab5a23aa355b19f5066e593d38e13fb5cc6304a2439f671f61585fe8c4f4646f41c5b0b1a9867bbc77d7cbb55fba3404a56fef53d7e4fc55effca07fe3a040c6c3652c198edab6d37ecc099f433e79b8bd538bf6074f405f0565a71149f4713be781ca076fbef560408e7857c02efbb1b79321b81467db45e0ae04e9ed04e269d7f6781ceb0661927234be9ada7853dde9299a4ebf790ffa3c8c5f4cbb8a515222199d66fd6699c76ef -B 215M


#timeout $seconds zmap 8.147.0.0/16 --probe-ttl=$ttl -M udp -O csv -s 65535 -p 1-65534 --probe-args=hex:c300000001ff2a9dba84bba7f0e5aa525d21ec77dbfdb981c25d59f40bea6dbf44e3b52db08cb3877e380d77aad3e8b0b87da966e04a969a3db60cc61a4b4681862b3ee02a6ec513cbaf0209e0eacbd0f97064882ce22abb2f941879f531906e833510f289731b7664e04bb06147b4f0927b827d0f3280b8c0b0bf01fd7d494ddddd3ff7f2318947312678baba7a93560036187947e83304f58c859070312b6a193851912cd9053390ef1a5b6d281b19bb13c326c67b2f51abb3648096f9f95c86a2a0ff79bb7eedbb9c3dce106aa9c8f2606db4d3b20bd895daded95d44dd0ac0061a805fdb2353fd570e95b965ef1a05c8a2336802ae99fec14b7329dc4c00d6fb0d35f600004055178400155dbbc01529e95cb7b0ff44f0bb5740ff573ef7d12586619f36a5d642ff85b5394ef7283dfdc15bba07d413b8d660017c88a9ec9cc510a359a1e7aaca5f807e255fa120566c7857eb8c78a3449243097ece -B 1000M
