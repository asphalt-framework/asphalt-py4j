Version history
===============

This library adheres to `Semantic Versioning 2.0 <http://semver.org/>`_.

**4.0.0** (2023-12-26)

- **BACKWARD INCOMPATIBLE** Bumped minimum Asphalt version to 4.8
- **BACKWARD INCOMPATIBLE** Refactored component to only provide a single Java gateway
  (you will have to add two components to get two Java gateways)
- **BACKWARD INCOMPATIBLE** Dropped the context attribute (use dependency injection
  instead)
- Dropped explicit run-time type checking
- Dropped support for Python 3.7 (and earlier)

**3.0.1** (2017-06-04)

- Added compatibility with Asphalt 4.0

**3.0.0** (2017-04-11)

- **BACKWARD INCOMPATIBLE** Migrated to Asphalt 3.0 and py4j 0.10.4+

**2.0.0** (2016-05-11)

- **BACKWARD INCOMPATIBLE** Migrated to Asphalt 2.0
- Allowed combining ``gateways`` with default parameters

**1.1.0** (2016-01-02)

- Added typeguard checks to fail early if arguments of wrong types are passed to functions

**1.0.1** (2015-11-20)

- Fixed the Asphalt dependency specification to work with setuptools older than 8.0

**1.0.0** (2015-05-16)

- Initial release
