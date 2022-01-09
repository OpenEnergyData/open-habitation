# Open Habitation API

This is a project started at the [Energy Data Hackdays 2021](https://energydatahackdays.ch/). Please see our [project page](https://hack.opendata.ch/project/779) for background and have fun.

## Service

This repository contains a minimal backend service API based on the [Falcon](http://falconframework.org/) framework, [Pandas DataPackage Reader](https://github.com/rgieseke/pandas-datapackage-reader), and the [Falcon plugin](https://github.com/alysivji/falcon-apispec) for [apispec](https://apispec.readthedocs.io/en/latest/index.html).

Use pip with `requirements.txt` or install the [Poetry](https://python-poetry.org/) dependency manager, and:

```
poetry install
poetry shell
python api.py
```

To update the requirements file:

```
poetry export --without-hashes -f requirements.txt > requirements.txt
```



## License

This package is licensed by its maintainers under the MIT License.

If you intended to use these data in a public or commercial product, please
check the data sources themselves for any specific restrictions.
