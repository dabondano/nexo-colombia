# Certificates for www.funcionpublica.gov.co

`letsencrypt-yr1-chain.pem` holds two public certificates of Let's Encrypt:
the intermediate "YR1" and "Root YR" as signed by "ISRG Root X1".

Why they are here: on 2026-11-17 the web server of Función Pública sent its own
certificate without the intermediate that issued it, so a client that does not
fetch missing certificates by itself (as browsers do) cannot verify the
connection. With these two certificates the connection is verified in the normal
way, up to the ISRG Root X1 certificate that the operating system already trusts.
Certificate verification is never switched off.

They were taken from https://letsencrypt.org/certificates/ and checked with
`openssl verify` against the system's trusted roots. If the server changes its
certificate issuer, the download fails with a certificate error and this file
must be reviewed.
