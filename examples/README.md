# Example Configurations

## Oauth2 Single Sign On

Modify [helmValues-oauth2-proxy.yaml](helmValues-oauth2-proxy.yaml) and install with:

```bash
helm upgrade --install oauth2-proxy-porthole oauth2-proxy \                                                               
    --repo https://oauth2-proxy.github.io/manifests \
    -f helmValues-oauth2-proxy.yaml
```
