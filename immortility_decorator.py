from loguru import logger
import random

def error_handler(num: int = 1, parrent_exception = BaseException):
    """
    Decorator which catches all possible errors and enables to re-run the function.

    :param num: (optional) integer number, enables retrying to run the function, default = 1.
    """
    def exception_decorator(fun):
        """
        Decorator which operates the function

        :param fun: function which has been decorated.
        """
        logger.info('Exception Decorator Starts.') 
        def tolerate_errors(*args,**kwargs):
            """
            Wrapper which takes all input arguments and passes it to the function.

            :param *args: All input arguments.
            :param **kwargs: All input keyword arguments.
            """
            errors = []
            for i in range(num):
                try: # tested function.
                    fun(*args,**kwargs)
                except parrent_exception as e: # what happens if DEFINED EXCEPTION OCCURS.
                    logger.critical(f'Exception caught: {e}')
                    errors.append(e)
                    continue
                except:
                    logger.critical(f'Unknown error occured ...')
                    errors.append('UNKNOWN ERROR')
                else: # what happens if NO EXCEPTION OCCURS.
                    logger.info('else statement was executed. No exception occured.')
                    break
                finally: # what happens ALWAYS (no matter if exception occurs or not).
                    logger.info(f'finally statement: Attempt {i+1}/{num}')
            logger.debug(f'While running the function: {fun.__name__} with arguments: {args} and keyword arguments: {kwargs} the following errors occured: {errors} necessary attempts: {i+1}/{num}')
        return tolerate_errors
    return exception_decorator

def exception_generator(parent_error = BaseException):
    all_errors = []
    def loop_elements(err: list) -> list:
        """ Loops over all subclasses of the input exception and lists them."""
        for i in range(len(err)):
            err_sub = [*err[i].__subclasses__()]
            if len(err_sub) >= 1:
                all_errors.append(err[i])
                loop_elements(err_sub)
            elif len(err_sub) == 0:
                all_errors.append(err[i])
                continue
    loop_elements([parent_error])
    return all_errors

# @error_handler(5)
def random_error_emulator(error_propability: float = 1.0, parent_err = BaseException):
    """
    Raises random Exception inherited from (and including) BaseException class, if not other specified with parent_error parameter.
    Prints a list of all inherited exceptions (including parent_error parameter) when no error was raised.

    :param error_propability: float number 0-1 to control how propable it is, that this function raises an random error.
    :raise: raises a random exception inherited from input exception.
    """
    all_errs = exception_generator(parent_err)
    
    if random.uniform(0,1) < error_propability:
        print(f'Error raised by {random_error_emulator.__name__} ...')
        raise all_errs[random.randint(0,len(all_errs)-1)]
    else:
        print(f'no error raised by {random_error_emulator.__name__} ...')
        # print(f'\nall errors:\n{all_errs}')
        print(f'(number of all errors: {len(all_errs)})\n')


if __name__ == '__main__':
    # print(exception_generator())
    random_error_emulator(error_propability=1, parent_err=BaseException)