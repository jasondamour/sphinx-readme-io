Configuration Guide
===================

This guide covers all configuration options available in the project.

Learn how to customize every aspect of the project behavior.

Environment Variables
---------------------

You can configure the project using environment variables:

``MY_PROJECT_DEBUG``
    Enable debug mode (default: ``false``)

``MY_PROJECT_LOG_LEVEL``
    Set logging level (default: ``INFO``)

Configuration File
------------------

Create a ``config.yaml`` file:

.. code-block:: yaml

   project:
     name: "My Project"
     debug: true
     
   logging:
     level: DEBUG
     format: "%(asctime)s - %(message)s"

Related Documents
-----------------

* :doc:`../getting-started` - Initial setup guide
* :doc:`../api/index` - Full API reference
