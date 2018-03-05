import json
from rdsslib.kinesis.decorators import (
    RouterHistoryDecorator,
)

CodeMalformedBody = 'GENERR001'
CodeUnsupportedMessageType = 'GENERR002'
CodeExpiredMessage = 'GENERR003'
CodeMalformedHeader = 'GENERR004'
CodeMaxConnectionTries = 'GENERR005'
CodeUnderlyingSystemError = 'GENERR006'
CodeMalformedJsonBody = 'GENERR007'
CodeFailedTransactionRollback = 'GENERR008'
CodeUnknownError = 'GENERR009'
CodeMaxMessageSendTries = 'GENERR010'
CodeResourceNotFound = 'GENERR011'
CodeResourceAlreadyExists = 'GENERR012'
CodeSDKLibraryError = 'GENERR013'

_errors = {
    CodeMalformedBody: 'The Message Body is not in the expected format, '
                       'for example mandatory fields are missing.',
    CodeUnsupportedMessageType: 'The provided messageType is not supported.',
    CodeExpiredMessage: 'The expiration date of the Message had passed at'
                        ' the point at which delivery was attempted.',
    CodeMalformedHeader: 'Invalid, missing or corrupt headers were detected '
                         'on the Message.',
    CodeMaxConnectionTries: 'Maximum number of connection retries exceeded '
                            'when attempting to send the Message.',
    CodeUnderlyingSystemError: 'An error occurred interacting with the '
                               'underlying system.',
    CodeMalformedJsonBody: 'Malformed JSON was detected in the Message Body.',
    CodeFailedTransactionRollback: 'An attempt to roll back a '
                                   'transaction failed.',
    CodeUnknownError: 'An unexpected or unknown error occurred.',
    CodeMaxMessageSendTries: 'Maximum number of Message resend'
                             'retries exceeded.',
    CodeResourceNotFound: 'Resource not found',
    CodeResourceAlreadyExists: 'Resource already exists',
    CodeSDKLibraryError: 'SDK level error',
}


class BaseError(Exception):
    code = None

    def __init__(self, details=None):
        self.details = details

    def export(self):
        decorated = json.loads(RouterHistoryDecorator().process('{}'))
        decorated_header_with_error = dict(
            decorated['messageHeader'], **{
                'messageType': 'Error',
                'errorCode': self.code,
                'errorDescription': _errors[self.code] + ' ' + (self.details or ''),
            }
        )
        return dict(
            decorated, **{
                'messageHeader': decorated_header_with_error,
                'messageBody': {},
            }
        )


class MalformedBodyError(BaseError):
    code = CodeMalformedBody


class UnsupportedMessageTypeError(BaseError):
    code = CodeUnsupportedMessageType


class ExpiredMessageError(BaseError):
    code = CodeExpiredMessage


class MalformedHeaderError(BaseError):
    code = CodeMalformedHeader


class MaxConnectionTriesError(BaseError):
    code = CodeMaxConnectionTries


class UnderlyingSystemError(BaseError):
    code = CodeUnderlyingSystemError


class MalformedJsonBodyError(BaseError):
    code = CodeMalformedJsonBody


class FailedTransactionRollbackError(BaseError):
    code = CodeFailedTransactionRollback


class UnknownErrorError(BaseError):
    code = CodeUnknownError


class MaxMessageSendTriesError(BaseError):
    code = CodeMaxMessageSendTries


class ResourceNotFoundError(BaseError):
    code = CodeResourceNotFound


class ResourceAlreadyExistsError(BaseError):
    code = CodeResourceAlreadyExists


class SDKLibraryError(BaseError):
    code = CodeSDKLibraryError
