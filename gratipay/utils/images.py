# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import zipfile
from cStringIO import StringIO

import requests


def imgize(image, image_type):
    large = None
    small = None
    crops = requests.post( 'http://gip.rocks/v1',
                           data=image,
                           headers={'Content-Type': image_type})

    if crops.status_code == 200:
        zf = zipfile.ZipFile(StringIO(crops.content))
        large = zf.open('160').read()
        small = zf.open('48').read()
        return large, small
    elif crops.status_code == 413:
        raise ImageTooLarge
    elif crops.status_code == 415:
        raise InvalidImageType
    else:
        raise UnknownImageError


class BadImage(Exception): pass
class ImageTooLarge(BadImage): pass
class InvalidImageType(BadImage): pass
class UnknownImageError(Exception): pass


def get_default_for_oid(db, oid, size):
    db.all('''
        SELECT id
          FROM teams
         WHERE image_oid_original=%s
            OR image_oid_large=%s
            OR image_oid_small FROM teams WHERE
    ''')


class HasImage(object):
    """Mixin for models to store an image.

    Assumes these fields (oid DEFAULT 0 NOT NULL):

        image_oid_original
        image_oid_large
        image_oid_small
        image_type

    """

    IMAGE_SIZES = ('original', 'large', 'small')

    def get_oid_for_size(self, size):
        return getattr(self, 'image_oid_{}'.format(size))

    def get_image_url(self, size):
        assert size in self.IMAGE_SIZES, size
        return '/images/{}/{}'.format(self.get_oid_for_size(size), size)

    def save_image(self, original, large, small, image_type):
        with self.db.get_cursor() as c:
            oids = {}
            for size in self.IMAGE_SIZES:
                lobject = c.connection.lobject(self.get_oid_for_size(size), mode='wb')
                lobject.write(locals()[size])
                oids[size] = lobject.oid
                lobject.close()

            c.run("""UPDATE """ + self.typname + """
                        SET image_oid_original=%s, image_oid_large=%s, image_oid_small=%s
                          , image_type=%s
                      WHERE id=%s"""
                 , (oids['original'], oids['large'], oids['small'], image_type, self.id)
                  )
            self.app.add_event(c, 'team', dict( action='upsert_image'
                                              , id=self.id
                                              , **oids
                                               ))
            self.set_attributes( image_type=image_type
                               , **{'image_oid_'+size: oids[size] for size in oids}
                                )
            return oids

    def load_image(self, size):
        assert size in self.IMAGE_SIZES, size
        image = None
        oid = getattr(self, 'image_oid_{}'.format(size))
        if oid != 0:
            with self.db.get_connection() as c:
                image = c.lobject(oid, mode='rb').read()
        return image
