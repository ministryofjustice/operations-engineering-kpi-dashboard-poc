FROM grafana/grafana:10.4.2-ubuntu

# Disable Login form or not
ENV GF_AUTH_DISABLE_LOGIN_FORM "true"
# Allow anonymous authentication or not
ENV GF_AUTH_ANONYMOUS_ENABLED "true"
# Role of anonymous user
ENV GF_AUTH_ANONYMOUS_ORG_ROLE "Admin"
# Install plugins here our in your own config file
ENV GF_INSTALL_PLUGINS="marcusolsson-csv-datasource"

# Copy CSV Data Into Grafana
COPY ./data /data/

# Add provisioning
ADD ./grafana/provisioning /etc/grafana/provisioning
# Add configuration file
ADD ./grafana/grafana.ini /etc/grafana/grafana.ini
# Add dashboard json files
ADD ./grafana/dashboards /etc/grafana/dashboards
