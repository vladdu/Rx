use strict;
use warnings;
package Data::Rx::CoreType::bool;
use base 'Data::Rx::CoreType';
# ABSTRACT: the Rx //bool type

sub validate {
  my ($self, $value) = @_;

  return 1 if (
    defined($value)
    and ref($value)
    and (
      eval { $value->isa('JSON::XS::Boolean') }
      or
      eval { $value->isa('JSON::PP::Boolean') }
      or
      eval { $value->isa('boolean') }
    )
  );

  $self->fail({
    error   => [ qw(type) ],
    message => "found value was not a bool",
    value   => $value,
  });
}

sub subname   { 'bool' }

1;
