from django.conf.urls import patterns, include, url

from warehouse.api import Api

import warehouse.api.v1.resources

v1_api = Api(api_name="v1")
v1_api.register(warehouse.api.v1.resources.ProjectResource())
v1_api.register(warehouse.api.v1.resources.VersionResource())
v1_api.register(warehouse.api.v1.resources.FileResource())
v1_api.register(warehouse.api.v1.resources.SearchResource())

urlpatterns = patterns("",
    url(r"^last-modified/?$", "warehouse.api.simple.views.last_modified", name="last_modified"),
    url(r"^simple/", include("warehouse.api.simple.urls")),
    url(r"^restricted/", include("warehouse.api.simple.restricted")),
    url(r"", include(v1_api.urls)),
)
