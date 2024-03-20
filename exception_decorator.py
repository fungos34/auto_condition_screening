from loguru import logger
import random
import numpy as np
import functools
import inspect

def error_handler(repititions: int = 0, parrent_exception = BaseException):
    """
    Decorator which catches all possible errors and enables to re-run the function.

    :param repititions: (optional) integer number, enables retrying to run the function, default = 1.
    """
    def exception_decorator(fun):
        """
        Decorator which operates the function

        :param fun: function which has been decorated.
        """
        logger.info(f'Exception decorator launched for {fun.__name__}.') 
        
        if inspect.iscoroutinefunction(fun):
            @functools.wraps(fun)
            async def async_tolerate_errors(*args,**kwargs):
                """
                Wrapper which takes all input arguments and passes it to the function.

                :param *args: All input arguments.
                :param **kwargs: All input keyword arguments.
                """
                errors = []
                i = 0
                while i <= repititions:
                    i += 1
                    try: # tested function.
                        await fun(*args,**kwargs)
                    except parrent_exception as e: # what happens if DEFINED EXCEPTION OCCURS.
                        logger.critical(f'Exception caught: {e}')
                        errors.append(e)
                        continue
                    except:
                        logger.critical(f'Unknown error occured ...')
                        errors.append('UNKNOWN ERROR')
                    else: # what happens if NO EXCEPTION OCCURS.
                        logger.info('No exception occured.')
                        break
                    finally: # what happens ALWAYS (no matter if exception occurs or not).
                        logger.info(f'Attempt {i}/{repititions+1}')
                logger.info(f'During function execution with local name space {locals()} the following errors occured: {errors} necessary attempts: {i}/{repititions+1}')
                logger.info(f'Exception decorator abandoned for {fun.__name__}.\n\n') 
            return async_tolerate_errors
        else:
            @functools.wraps(fun)
            def sync_tolerate_errors(*args,**kwargs):
                """
                Wrapper which takes all input arguments and passes it to the function.

                :param *args: All input arguments.
                :param **kwargs: All input keyword arguments.
                """
                errors = []
                i = 0
                while i <= repititions:
                    i += 1
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
                        logger.info('No exception occured.')
                        break
                    finally: # what happens ALWAYS (no matter if exception occurs or not).
                        logger.info(f'Attempt {i}/{repititions+1}')
                logger.info(f'During function execution with local name space {locals()} the following errors occured: {errors} necessary attempts: {i}/{repititions+1}')
                logger.info(f'Exception decorator abandoned for {fun.__name__}.\n\n')
            return sync_tolerate_errors
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
    random_error_emulator(error_propability=0, parent_err=BaseException)