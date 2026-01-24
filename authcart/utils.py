from django.contrib.auth.tokens import PasswordResetTokenGenerator
import six

class TokenGenerator(PasswordResetTokenGenerator):
    def __make_hash_value(self,user,timestamp):
        return (six.test_type(user.pk)+six.test_type(timestamp)+six.test_type(user.is_activate))
generate_token=TokenGenerator()