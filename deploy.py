# -*- coding: utf-8 -*-
import configparser, pathlib, os

working_directory = pathlib.Path(__file__).resolve().parents[0]

config = configparser.ConfigParser()
config.read(str(working_directory/"preferences"))

working_directory = str(working_directory)

server_host = config.get("server", "host")
server_port = config.get("server", "port")
server_domain = config.get("server", "domain")

supervisor_config = '''[program:platform]
command = python3 {working_directory}/server/main.py
directory = {working_directory}
user = ubuntu
stdout_logfile= {working_directory}/log/error.log
loglevel = info
redirect_stderr = true
environment = LANG="en_US.utf8", LC_ALL="en_US.UTF-8", LC_LANG="en_US.UTF-8"
'''.format(working_directory = working_directory)

supervisor_conf = open("supervisor.conf","w")
supervisor_conf.write(supervisor_config)
supervisor_conf.close()
supervisor_conf_symbolic_link = "/etc/supervisor/conf.d/platform.conf"
if os.path.exists(supervisor_conf_symbolic_link): os.remove(supervisor_conf_symbolic_link)
os.system("sudo ln -s {working_directory}/supervisor.conf {supervisor_conf_symbolic_link}".format(
    working_directory = working_directory,
    supervisor_conf_symbolic_link = supervisor_conf_symbolic_link
))

nginx_config = '''# PLATFORM SERVER

server {{

	listen 443;
	server_name {server_domain};
	server_name_in_redirect off;

	ssl on;
	ssl_certificate /etc/letsencrypt/live/{server_domain}/fullchain.pem;
	ssl_certificate_key /etc/letsencrypt/live/{server_domain}/privkey.pem;

	ssl_session_timeout 10m;
	ssl_session_cache shared:SSL:10m;

	ssl_protocols  TLSv1 TLSv1.1 TLSv1.2;
	ssl_ciphers 'AES128+EECDH:AES128+EDH';
	ssl_prefer_server_ciphers on;

	if ($host != $server_name){{ return 444; }}

	default_type	"";

	### root ###

	location = / {{
		rewrite	/index.html	last;
	}}
	location ~* ^/[^/]+$ {{
		root	{working_directory}/root/;
	}}

	### static ###
	
	location  /static/ {{
		alias	{working_directory}/static/;
	}}

	### memberlist ###

	location = /data/memberlist {{
		set $type "all";
		if ($args ~* "((?<=&)|(?<=^))group=nogizaka((?=$)|(?=&))"){{
			set $type "nogizaka";
		}}
		if ($args ~* "((?<=&)|(?<=^))group=keyakizaka((?=$)|(?=&))"){{
			set $type "keyakizaka";
		}}
		alias	{working_directory}/file/$type.json;
		add_header Content-Type 'application/json; charset=utf-8';
	}}

	### update ###

	location = /check/version/android {{
		alias	{working_directory}/update/android.json;
		add_header Content-Type 'application/json; charset=utf-8';
	}}

	### apk ###

	location /download/apk/ {{
		alias	{working_directory}/update/;
		# add_header Content-Type 'application/json; charset=utf-8';
	}}
	
	### forward ###

	location = /data/blogs {{
		proxy_pass		https://aidoru.tk;
		proxy_redirect		off;
		proxy_set_header	REMOTE-HOST $remote_addr;
	}}

	### photo ###

	location /photo/ {{
		alias	{working_directory}/photo/;
		#autoindex on;
		#autoindex_exact_size off;
		#autoindex_localtime on;
	}}

	### proxy ###

	location / {{
		proxy_pass	http://{server_host}:{server_port};
		proxy_redirect	off;
		access_log	{working_directory}/log/access.log;
	}}

	location /check/version/android {{
		proxy_pass	http://{server_host}:{server_port};
		proxy_redirect	off;
		access_log	{working_directory}/log/start.log;
	}}

	location ~ ^/view/\d+$   {{
		proxy_pass	http://{server_host}:{server_port};
		proxy_redirect	off;
		access_log	{working_directory}/log/view.log;
	}}

}}
'''.format(
    server_domain = server_domain,
    server_host = server_host,
    server_port = server_port,
    working_directory = working_directory
    )

nginx_conf = open("nginx.conf","w")
nginx_conf.write(nginx_config)
nginx_conf.close()
nginx_conf_symbolic_link = "/etc/nginx/sites-enabled/platform"
if os.path.exists(nginx_conf_symbolic_link): os.remove(nginx_conf_symbolic_link)
os.system("sudo ln -s {working_directory}/nginx.conf {nginx_conf_symbolic_link}".format(
    working_directory = working_directory,
    nginx_conf_symbolic_link = nginx_conf_symbolic_link
))

os.system("sudo service nginx restart")
os.system("sudo supervisorctl reload")