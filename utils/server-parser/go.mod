module server-parser

go 1.22.0

require common v1.0.0

replace common => ../common

require (
	github.com/gaukas/clienthellod v0.4.2
	github.com/google/gopacket v1.1.19
)

require (
	github.com/andybalholm/brotli v1.0.6 // indirect
	github.com/cloudflare/circl v1.3.7 // indirect
	github.com/gaukas/godicttls v0.0.4 // indirect
	github.com/klauspost/compress v1.17.8 // indirect
	github.com/refraction-networking/utls v1.6.6 // indirect
	golang.org/x/crypto v0.23.0 // indirect
	golang.org/x/sys v0.20.0 // indirect
)
