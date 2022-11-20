Raspberry Pi or similar with Linux

* Buttons server that uses named socket to send actions to other apps

More:[url]

* clone repo, setup keys.ini

* Installation, run `keys.py install` as root, it will copy files & dirs:
 - /etc/keys/keys.ini
 - /lib/systemd/system/keys.service
 - /usr/local/bin/keys.py
and execute:
 - systemctl enable keys.service
 - systemctl start keys.service
