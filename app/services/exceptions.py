class UserAlreadyExistsError(Exception):
    pass
class InvalidCredentialsError(Exception):
    pass
class InactiveUserError(Exception):
    pass
class InvalidPayerError(Exception):
    pass
class InvalidParticipantsError(Exception):
    pass
class GroupNotFound(Exception):
    pass
class PermissionDeniedError(Exception):
    pass
class UserNotFound(Exception):
    pass
class GroupMemberAlreadyExists(Exception):
    pass
class CannotRemoveSelfFromGroupError(Exception):
    pass