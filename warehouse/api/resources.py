from django.conf.urls import include, patterns, url

from tastypie.bundle import Bundle
from tastypie.resources import ModelResource as TastypieModelResource
from tastypie.utils import trailing_slash


__all__ = ["ModelResource"]


def _get_model_attr(obj, prefix, attr):
    for level in prefix:
        obj = getattr(obj, level)

    return getattr(obj, attr)


class ModelResource(TastypieModelResource):

    def base_urls(self):
        urls = [
            url(r"^(?P<resource_name>%s)%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_list'), name="api_dispatch_list"),
            url(r"^(?P<resource_name>%s)/(?P<%s>[^/]+)%s$" % (self._meta.resource_name, self._meta.detail_uri_name, trailing_slash()), self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]

        parent = getattr(self._meta, "parent_resource", None)
        child = self

        prefix = []

        while parent is not None:
            p = parent()
            include_pattern = patterns("", *urls)

            prefix.append(child._meta.parent_resource_uri_prefix)

            urls = [
                url(r"^%s/(?P<%s>[^/]+)/" % (p._meta.resource_name, "__".join(prefix[:] + [p._meta.detail_uri_name])), include(include_pattern)),
            ]

            child = parent
            parent = getattr(p._meta, "parent_resource", None)

        return urls

    def detail_uri_kwargs(self, bundle_or_obj):
        if isinstance(bundle_or_obj, Bundle):
            obj = bundle_or_obj.obj
        else:
            obj = bundle_or_obj

        uri_kwargs = super(ModelResource, self).detail_uri_kwargs(bundle_or_obj)

        parent = getattr(self._meta, "parent_resource", None)
        child = self

        prefix = []

        while parent is not None:
            p = parent()

            prefix.append(child._meta.parent_resource_uri_prefix)

            uri_kwargs.update({
                "__".join(prefix[:] + [p._meta.detail_uri_name]): _get_model_attr(obj, prefix, p._meta.detail_uri_name),
            })

            child = parent
            parent = getattr(p._meta, "parent_resource", None)

        return uri_kwargs