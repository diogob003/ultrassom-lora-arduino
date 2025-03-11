# Monitoramento de nível de fluido remoto com comunicação LoRa

Projeto proposto na disciplina de **Teleinformática e Redes 2** do [**Departamento de Ciência da Computação**](https://cic.unb.br/) da [**Universidade Federal de Brasília**](https://www.unb.br/).

## Componentes utilizados
* Arduino UNO
* Sensor ultrassom HC-SR04
* Conversor USB → UART, RS232 e TTL, chip CP2102
* 2 módulos LoRa EBYTE E32-900T30D
* 2 antenas SMA omnidirecional 5 dBi
* 3 resistores de 1 kΩ

<img src="https://github.com/diogob003/ultrassom-lora-arduino/blob/screenshots/diagrama0.png">

<img src="https://github.com/diogob003/ultrassom-lora-arduino/blob/screenshots/img1.png">

## Instalação das dependências
São elas:
- [Python v3.10+](https://www.python.org/)
- [Gtk v4.1+](https://www.gtk.org/) - interface gráfica
- [PyGObject v3.40+](https://pygobject.gnome.org/getting_started.html) - bindings (para Gtk)
- [PySerial v3.5+](https://github.com/pyserial/pyserial) - comunicação serial
- [MatPlotLib v3.1+](https://matplotlib.org/) - gráficos

### no MacOS
- Primeiro instale gerenciador de pacotes [MacPorts](https://www.macports.org/install.php) e depois
```sh
sudo port install git python312 gtk4 py312-gobject3 py312-serial py312-matplotlib
sudo port select --set python3 python312
```

### no Ubuntu
```sh
sudo apt install git python3 libgtk-4-1 python3-gi python3-serial python3-matplotlib python3-gi-cairo gir1.2-gtk-4.0
```

### no Windows
- Primeiro instale o gerenciador de pacotes [Msys2](https://www.msys2.org/)
- Em seguida abra o terminal `ucrt64` e instale as dependências
```sh
pacman -S git mingw-w64-ucrt-x86_64-python3 mingw-w64-ucrt-x86_64-gtk4 mingw-w64-ucrt-x86_64-python-gobject mingw-w64-ucrt-x86_64-python-pyserial mingw-w64-ucrt-x86_64-python-matplotlib
```

## Como iniciar o aplicativo?
Após instalar as dependências, basta clonar o repositório e executar o arquivo `main.py`
```sh
git clone https://github.com/diogob003/ultrassom-lora-arduino.git
cd ultrassom-lora-arduino/gui-app/
python3 main.py
```
## Como programar o Arduino?
1. Instale as seguintes bibliotecas na IDE Arduino:
    * [EBYTE](https://github.com/KrisKasprzak/EBYTE)
    * [Bifrost.Arduino.Sensors.HCSR04](https://github.com/jeremylindsayni/Bifrost.Arduino.Sensors.HCSR04)
2. Abra [sensor_nivel.ino](https://github.com/diogob003/ultrassom-lora-arduino/blob/master/sensor_nivel/sensor_nivel.ino) na IDE
3. Faça upload do código para o Arduino

## License
This project is licensed under the terms of the [MIT](https://choosealicense.com/licenses/mit/) license.